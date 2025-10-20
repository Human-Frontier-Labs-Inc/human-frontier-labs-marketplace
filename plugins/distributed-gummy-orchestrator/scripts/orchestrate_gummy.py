#!/usr/bin/env python3
"""
Orchestrate gummy-agent tasks across distributed network using 'd' command.
Handles load balancing, task distribution, and network-wide coordination.
"""

import subprocess
import json
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def run_d_command(cmd: str) -> Tuple[str, int]:
    """
    Execute 'dw' command and return output.

    Args:
        cmd: Full command string (e.g., "dw status")

    Returns:
        Tuple of (stdout, returncode)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except Exception as e:
        return f"Error: {e}", -1


def get_load_metrics() -> Dict:
    """
    Get load metrics from 'dw load' command.

    Returns:
        Dict mapping host -> metrics:
        {
            'host1': {'cpu': 15, 'mem': 45, 'load': 0.23, 'score': 0.28},
            'host2': {...},
        }
    """
    output, code = run_d_command("dw load")

    if code != 0:
        return {}

    metrics = {}

    # Parse dw load output
    # Expected format:
    # host1    CPU: 15%  MEM: 45%  LOAD: 0.23  SCORE: 0.28
    for line in output.strip().split('\n'):
        if not line.strip():
            continue

        # Extract host and metrics
        match = re.match(r'(\S+)\s+CPU:\s*(\d+)%\s+MEM:\s*(\d+)%\s+LOAD:\s*([\d.]+)\s+SCORE:\s*([\d.]+)', line)
        if match:
            host, cpu, mem, load, score = match.groups()
            metrics[host] = {
                'cpu': int(cpu),
                'mem': int(mem),
                'load': float(load),
                'score': float(score)
            }

    return metrics


def get_host_status() -> Dict:
    """
    Get host availability from 'dw status' command.

    Returns:
        Dict mapping host -> status:
        {
            'host1': {'status': 'online', 'ip': '100.1.2.3'},
            'host2': {'status': 'offline'},
        }
    """
    output, code = run_d_command("dw status")

    if code != 0:
        return {}

    status = {}

    # Parse dw status output
    # Expected format:
    # host1    online   100.1.2.3
    # host2    offline  -
    for line in output.strip().split('\n'):
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) >= 2:
            host = parts[0]
            state = parts[1]
            ip = parts[2] if len(parts) > 2 else None

            status[host] = {
                'status': state,
                'ip': ip
            }

    return status


def select_optimal_host(
    task_type: Optional[str] = None,
    exclude: Optional[List[str]] = None
) -> Optional[Dict]:
    """
    Select the best host for a task based on load metrics.

    Args:
        task_type: Type of task ('database', 'api', 'frontend', etc.)
        exclude: List of hosts to exclude from selection

    Returns:
        Dict with selected host info:
        {
            'host': 'node-1',
            'score': 0.23,
            'cpu': 15,
            'mem': 45,
            'load': 0.23
        }

    Example:
        >>> optimal = select_optimal_host(task_type="database")
        >>> print(f"Selected: {optimal['host']}")
        Selected: node-1
    """
    exclude = exclude or []

    # Get current load metrics
    load_data = get_load_metrics()

    # Get host availability
    status_data = get_host_status()

    # Filter to online hosts not in exclude list
    available_hosts = [
        host for host, info in status_data.items()
        if info['status'] == 'online' and host not in exclude
    ]

    if not available_hosts:
        return None

    # Filter load data to available hosts
    available_load = {
        host: metrics
        for host, metrics in load_data.items()
        if host in available_hosts
    }

    if not available_load:
        # No load data, pick first available
        host = available_hosts[0]
        return {
            'host': host,
            'score': 0.5,  # Unknown
            'cpu': None,
            'mem': None,
            'load': None
        }

    # Select host with lowest score (best performance)
    best_host = min(available_load.keys(), key=lambda h: available_load[h]['score'])
    best_metrics = available_load[best_host]

    return {
        'host': best_host,
        'score': best_metrics['score'],
        'cpu': best_metrics['cpu'],
        'mem': best_metrics['mem'],
        'load': best_metrics['load']
    }


def sync_codebase(host: str, local_path: str, remote_path: Optional[str] = None) -> bool:
    """
    Sync codebase to remote host using 'dw sync'.

    Args:
        host: Target host name
        local_path: Local directory to sync
        remote_path: Remote path (defaults to same as local)

    Returns:
        True if sync successful
    """
    if remote_path is None:
        remote_path = local_path

    # Change to local path
    original_dir = os.getcwd()

    try:
        os.chdir(local_path)

        # Execute dw sync
        output, code = run_d_command(f"dw sync {host}")

        return code == 0
    finally:
        os.chdir(original_dir)


def execute_remote_gummy(
    host: str,
    task: str,
    project_path: str,
    sync_first: bool = True
) -> Dict:
    """
    Execute gummy task on remote host.

    Args:
        host: Target host name
        task: Gummy task description
        project_path: Path to project directory
        sync_first: Whether to sync codebase before executing

    Returns:
        Dict with execution info:
        {
            'host': 'node-1',
            'task': 'optimize queries',
            'command': 'cd ... && gummy task ...',
            'synced': True,
            'launched': True
        }
    """
    result = {
        'host': host,
        'task': task,
        'synced': False,
        'launched': False
    }

    # Sync if requested
    if sync_first:
        result['synced'] = sync_codebase(host, project_path)
        if not result['synced']:
            return result

    # Build gummy command
    gummy_cmd = f'cd {project_path} && gummy task "{task}"'

    # Execute on remote host
    full_cmd = f'dw run {host} \'{gummy_cmd}\''
    result['command'] = full_cmd

    output, code = run_d_command(full_cmd)
    result['launched'] = (code == 0)
    result['output'] = output

    return result


def sync_and_execute_gummy(
    host: str,
    task: str,
    project_dir: str
) -> Dict:
    """
    Convenience function: sync codebase and execute gummy task.

    Args:
        host: Target host name
        task: Gummy task description
        project_dir: Project directory path

    Returns:
        Execution result dict
    """
    return execute_remote_gummy(host, task, project_dir, sync_first=True)


def parallel_gummy_tasks(tasks: List[Dict]) -> List[Dict]:
    """
    Execute multiple gummy tasks in parallel across hosts.

    Args:
        tasks: List of task dicts:
            [
                {'host': 'node-1', 'task': 'task1', 'project': '/path'},
                {'host': 'node-2', 'task': 'task2', 'project': '/path'},
            ]

    Returns:
        List of result dicts
    """
    results = []

    for task_info in tasks:
        result = execute_remote_gummy(
            host=task_info['host'],
            task=task_info['task'],
            project_path=task_info['project'],
            sync_first=task_info.get('sync', True)
        )
        results.append(result)

    return results


def monitor_all_specialists() -> Dict:
    """
    Get status of all specialists across all hosts.

    Returns:
        Dict mapping host -> specialists:
        {
            'node-1': [
                {'name': 'database-expert', 'status': 'active', 'sessions': 8},
                {'name': 'api-developer', 'status': 'dormant', 'sessions': 3},
            ],
            'node-2': [...],
        }
    """
    status_data = get_host_status()
    online_hosts = [h for h, info in status_data.items() if info['status'] == 'online']

    all_specialists = {}

    for host in online_hosts:
        # Check if gummy is installed
        check_cmd = f'dw run {host} "command -v gummy"'
        output, code = run_d_command(check_cmd)

        if code != 0:
            continue

        # List specialists
        list_cmd = f'dw run {host} "ls -1 ~/.gummy/specialists 2>/dev/null || echo"'
        output, code = run_d_command(list_cmd)

        if code != 0 or not output.strip():
            continue

        specialists = []
        for spec_name in output.strip().split('\n'):
            if not spec_name:
                continue

            # Get specialist metadata
            meta_cmd = f'dw run {host} "cat ~/.gummy/specialists/{spec_name}/meta.yaml 2>/dev/null"'
            meta_output, meta_code = run_d_command(meta_cmd)

            if meta_code == 0:
                # Parse YAML (simple key: value format)
                spec_info = {'name': spec_name}
                for line in meta_output.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        spec_info[key.strip()] = value.strip()

                specialists.append(spec_info)

        if specialists:
            all_specialists[host] = specialists

    return all_specialists


def comprehensive_distributed_report() -> Dict:
    """
    Generate comprehensive report of entire distributed network.

    Returns:
        Dict with complete network state:
        {
            'timestamp': '2025-10-19T22:00:00',
            'hosts': {...},
            'load': {...},
            'specialists': {...},
            'summary': 'Summary text'
        }
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'hosts': get_host_status(),
        'load': get_load_metrics(),
        'specialists': monitor_all_specialists()
    }

    # Generate summary
    online_count = sum(1 for h in report['hosts'].values() if h['status'] == 'online')
    total_count = len(report['hosts'])
    specialist_count = sum(len(specs) for specs in report['specialists'].values())

    report['summary'] = (
        f"{online_count}/{total_count} hosts online, "
        f"{specialist_count} active specialists"
    )

    return report


def main():
    """Test orchestration functions."""
    print("=" * 70)
    print("DISTRIBUTED GUMMY ORCHESTRATOR - TEST")
    print("=" * 70)

    # Test 1: Load metrics
    print("\n✓ Testing load metrics...")
    load = get_load_metrics()
    for host, metrics in load.items():
        print(f"  {host}: CPU {metrics['cpu']}%, Score {metrics['score']}")

    # Test 2: Host status
    print("\n✓ Testing host status...")
    status = get_host_status()
    for host, info in status.items():
        print(f"  {host}: {info['status']}")

    # Test 3: Optimal host selection
    print("\n✓ Testing optimal host selection...")
    optimal = select_optimal_host()
    if optimal:
        print(f"  Best host: {optimal['host']} (score: {optimal['score']})")
    else:
        print("  No hosts available")

    # Test 4: Specialist monitoring
    print("\n✓ Testing specialist monitoring...")
    specialists = monitor_all_specialists()
    for host, specs in specialists.items():
        print(f"  {host}: {len(specs)} specialists")
        for spec in specs:
            print(f"    - {spec['name']}")

    # Test 5: Comprehensive report
    print("\n✓ Testing comprehensive report...")
    report = comprehensive_distributed_report()
    print(f"  {report['summary']}")

    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
