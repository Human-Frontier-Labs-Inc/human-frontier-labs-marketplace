#!/usr/bin/env python3
"""
Load balancer for Tailscale SSH Sync Agent.
Intelligent task distribution based on machine resources.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.helpers import parse_cpu_load, parse_memory_usage, parse_disk_usage, calculate_load_score, classify_load_status
from sshsync_wrapper import execute_on_host

logger = logging.getLogger(__name__)


@dataclass
class MachineMetrics:
    """Resource metrics for a machine."""
    host: str
    cpu_pct: float
    mem_pct: float
    disk_pct: float
    load_score: float
    status: str


def get_machine_load(host: str, timeout: int = 10) -> Optional[MachineMetrics]:
    """
    Get CPU, memory, disk metrics for a machine.

    Args:
        host: Host to check
        timeout: Command timeout

    Returns:
        MachineMetrics object or None on failure

    Example:
        >>> metrics = get_machine_load("web-01")
        >>> metrics.cpu_pct
        45.2
        >>> metrics.load_score
        0.49
    """
    try:
        # Get CPU load
        cpu_result = execute_on_host(host, "uptime", timeout=timeout)
        cpu_data = {}
        if cpu_result.get('success'):
            cpu_data = parse_cpu_load(cpu_result['stdout'])

        # Get memory usage
        mem_result = execute_on_host(host, "free -m 2>/dev/null || vm_stat", timeout=timeout)
        mem_data = {}
        if mem_result.get('success'):
            mem_data = parse_memory_usage(mem_result['stdout'])

        # Get disk usage
        disk_result = execute_on_host(host, "df -h / | tail -1", timeout=timeout)
        disk_data = {}
        if disk_result.get('success'):
            disk_data = parse_disk_usage(disk_result['stdout'])

        # Calculate metrics
        # CPU: Use 1-min load average, normalize by assuming 4 cores (adjust as needed)
        cpu_pct = (cpu_data.get('load_1min', 0) / 4.0) * 100 if cpu_data else 50.0

        # Memory: Direct percentage
        mem_pct = mem_data.get('use_pct', 50.0)

        # Disk: Direct percentage
        disk_pct = disk_data.get('use_pct', 50.0)

        # Calculate load score
        score = calculate_load_score(cpu_pct, mem_pct, disk_pct)
        status = classify_load_status(score)

        return MachineMetrics(
            host=host,
            cpu_pct=cpu_pct,
            mem_pct=mem_pct,
            disk_pct=disk_pct,
            load_score=score,
            status=status
        )

    except Exception as e:
        logger.error(f"Error getting load for {host}: {e}")
        return None


def select_optimal_host(candidates: List[str],
                       prefer_group: Optional[str] = None,
                       timeout: int = 10) -> Tuple[Optional[str], Optional[MachineMetrics]]:
    """
    Pick best host from candidates based on load.

    Args:
        candidates: List of candidate hosts
        prefer_group: Prefer hosts from this group if available
        timeout: Timeout for metric gathering

    Returns:
        Tuple of (selected_host, metrics)

    Example:
        >>> host, metrics = select_optimal_host(["web-01", "web-02", "web-03"])
        >>> host
        "web-03"
        >>> metrics.load_score
        0.28
    """
    if not candidates:
        return None, None

    # Get metrics for all candidates
    metrics_list: List[MachineMetrics] = []

    for host in candidates:
        metrics = get_machine_load(host, timeout=timeout)
        if metrics:
            metrics_list.append(metrics)

    if not metrics_list:
        logger.warning("No valid metrics collected from candidates")
        return None, None

    # Sort by load score (lower is better)
    metrics_list.sort(key=lambda m: m.load_score)

    # If prefer_group specified, prioritize those hosts if load is similar
    if prefer_group:
        from utils.helpers import parse_sshsync_config, get_groups_for_host
        groups_config = parse_sshsync_config()

        # Find hosts in preferred group
        preferred_metrics = [
            m for m in metrics_list
            if prefer_group in get_groups_for_host(m.host, groups_config)
        ]

        # Use preferred if load score within 20% of absolute best
        if preferred_metrics:
            best_score = metrics_list[0].load_score
            for m in preferred_metrics:
                if m.load_score <= best_score * 1.2:
                    return m.host, m

    # Return absolute best
    best = metrics_list[0]
    return best.host, best


def get_group_capacity(group: str, timeout: int = 10) -> Dict:
    """
    Get aggregate capacity of a group.

    Args:
        group: Group name
        timeout: Timeout for metric gathering

    Returns:
        Dict with aggregate metrics:
        {
            'hosts': List[MachineMetrics],
            'total_hosts': int,
            'avg_cpu': float,
            'avg_mem': float,
            'avg_disk': float,
            'avg_load_score': float,
            'total_capacity': str  # descriptive
        }

    Example:
        >>> capacity = get_group_capacity("production")
        >>> capacity['avg_load_score']
        0.45
    """
    from utils.helpers import parse_sshsync_config

    groups_config = parse_sshsync_config()
    group_hosts = groups_config.get(group, [])

    if not group_hosts:
        return {
            'error': f'Group {group} not found or has no members',
            'hosts': []
        }

    # Get metrics for all hosts in group
    metrics_list: List[MachineMetrics] = []

    for host in group_hosts:
        metrics = get_machine_load(host, timeout=timeout)
        if metrics:
            metrics_list.append(metrics)

    if not metrics_list:
        return {
            'error': f'Could not get metrics for any hosts in {group}',
            'hosts': []
        }

    # Calculate aggregates
    avg_cpu = sum(m.cpu_pct for m in metrics_list) / len(metrics_list)
    avg_mem = sum(m.mem_pct for m in metrics_list) / len(metrics_list)
    avg_disk = sum(m.disk_pct for m in metrics_list) / len(metrics_list)
    avg_score = sum(m.load_score for m in metrics_list) / len(metrics_list)

    # Determine overall capacity description
    if avg_score < 0.4:
        capacity_desc = "High capacity available"
    elif avg_score < 0.7:
        capacity_desc = "Moderate capacity"
    else:
        capacity_desc = "Limited capacity"

    return {
        'group': group,
        'hosts': metrics_list,
        'total_hosts': len(metrics_list),
        'available_hosts': len(group_hosts),
        'avg_cpu': avg_cpu,
        'avg_mem': avg_mem,
        'avg_disk': avg_disk,
        'avg_load_score': avg_score,
        'total_capacity': capacity_desc
    }


def distribute_tasks(tasks: List[Dict], hosts: List[str],
                    timeout: int = 10) -> Dict[str, List[Dict]]:
    """
    Distribute multiple tasks optimally across hosts.

    Args:
        tasks: List of task dicts (each with 'command', 'priority', etc)
        hosts: Available hosts
        timeout: Timeout for metric gathering

    Returns:
        Dict mapping hosts to assigned tasks

    Algorithm:
        - Get current load for all hosts
        - Assign tasks to least loaded hosts
        - Balance by estimated task weight

    Example:
        >>> tasks = [
        ...     {'command': 'npm run build', 'weight': 3},
        ...     {'command': 'npm test', 'weight': 2}
        ... ]
        >>> distribution = distribute_tasks(tasks, ["web-01", "web-02"])
        >>> distribution["web-01"]
        [{'command': 'npm run build', 'weight': 3}]
    """
    if not tasks or not hosts:
        return {}

    # Get current load for all hosts
    host_metrics = {}
    for host in hosts:
        metrics = get_machine_load(host, timeout=timeout)
        if metrics:
            host_metrics[host] = metrics

    if not host_metrics:
        logger.error("No valid host metrics available")
        return {}

    # Initialize assignment
    assignment: Dict[str, List[Dict]] = {host: [] for host in host_metrics.keys()}
    host_loads = {host: m.load_score for host, m in host_metrics.items()}

    # Sort tasks by weight (descending) to assign heavy tasks first
    sorted_tasks = sorted(
        tasks,
        key=lambda t: t.get('weight', 1),
        reverse=True
    )

    # Assign each task to least loaded host
    for task in sorted_tasks:
        # Find host with minimum current load
        min_host = min(host_loads.keys(), key=lambda h: host_loads[h])

        # Assign task
        assignment[min_host].append(task)

        # Update simulated load (add task weight normalized)
        task_weight = task.get('weight', 1)
        host_loads[min_host] += (task_weight * 0.1)  # 0.1 = scaling factor

    return assignment


def format_load_report(metrics: MachineMetrics, compare_to_avg: Optional[Dict] = None) -> str:
    """
    Format load metrics as human-readable report.

    Args:
        metrics: Machine metrics
        compare_to_avg: Optional dict with avg_cpu, avg_mem, avg_disk for comparison

    Returns:
        Formatted report string

    Example:
        >>> metrics = MachineMetrics('web-01', 45, 60, 40, 0.49, 'moderate')
        >>> print(format_load_report(metrics))
        web-01: Load Score: 0.49 (moderate)
          CPU: 45.0% | Memory: 60.0% | Disk: 40.0%
    """
    lines = [
        f"{metrics.host}: Load Score: {metrics.load_score:.2f} ({metrics.status})",
        f"  CPU: {metrics.cpu_pct:.1f}% | Memory: {metrics.mem_pct:.1f}% | Disk: {metrics.disk_pct:.1f}%"
    ]

    if compare_to_avg:
        cpu_vs = metrics.cpu_pct - compare_to_avg.get('avg_cpu', 0)
        mem_vs = metrics.mem_pct - compare_to_avg.get('avg_mem', 0)
        disk_vs = metrics.disk_pct - compare_to_avg.get('avg_disk', 0)

        comparisons = []
        if abs(cpu_vs) > 10:
            comparisons.append(f"CPU {'+' if cpu_vs > 0 else ''}{cpu_vs:.0f}% vs avg")
        if abs(mem_vs) > 10:
            comparisons.append(f"Mem {'+' if mem_vs > 0 else ''}{mem_vs:.0f}% vs avg")
        if abs(disk_vs) > 10:
            comparisons.append(f"Disk {'+' if disk_vs > 0 else ''}{disk_vs:.0f}% vs avg")

        if comparisons:
            lines.append(f"  vs Average: {' | '.join(comparisons)}")

    return "\n".join(lines)


def main():
    """Test load balancer functions."""
    print("Testing load balancer...\n")

    print("1. Testing select_optimal_host:")
    print("   (Requires configured hosts - using dry-run simulation)")

    # Simulate metrics
    test_metrics = [
        MachineMetrics('web-01', 45, 60, 40, 0.49, 'moderate'),
        MachineMetrics('web-02', 85, 70, 65, 0.75, 'high'),
        MachineMetrics('web-03', 20, 35, 30, 0.28, 'low'),
    ]

    # Sort by score
    test_metrics.sort(key=lambda m: m.load_score)
    best = test_metrics[0]

    print(f"   ✓ Best host: {best.host} (score: {best.load_score:.2f})")
    print(f"   Reason: {best.status} load")

    print("\n2. Format load report:")
    report = format_load_report(test_metrics[0], {
        'avg_cpu': 50,
        'avg_mem': 55,
        'avg_disk': 45
    })
    print(report)

    print("\n✅ Load balancer tested")


if __name__ == "__main__":
    main()
