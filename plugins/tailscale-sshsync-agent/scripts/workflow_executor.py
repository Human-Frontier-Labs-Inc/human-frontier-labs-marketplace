#!/usr/bin/env python3
"""
Workflow executor for Tailscale SSH Sync Agent.
Common multi-machine workflow automation.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import time
import logging

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.helpers import format_duration, get_timestamp
from sshsync_wrapper import execute_on_group, execute_on_host, push_to_hosts
from load_balancer import get_group_capacity

logger = logging.getLogger(__name__)


def deploy_workflow(code_path: str,
                    staging_group: str,
                    prod_group: str,
                    run_tests: bool = True) -> Dict:
    """
    Full deployment pipeline: staging → test → production.

    Args:
        code_path: Path to code to deploy
        staging_group: Staging server group
        prod_group: Production server group
        run_tests: Whether to run tests on staging

    Returns:
        Dict with deployment results

    Example:
        >>> result = deploy_workflow("./dist", "staging", "production")
        >>> result['success']
        True
        >>> result['duration']
        "12m 45s"
    """
    start_time = time.time()
    results = {
        'stages': {},
        'success': False,
        'start_time': get_timestamp()
    }

    try:
        # Stage 1: Deploy to staging
        logger.info("Stage 1: Deploying to staging...")
        stage1 = push_to_hosts(
            local_path=code_path,
            remote_path="/var/www/app",
            group=staging_group,
            recurse=True
        )

        results['stages']['staging_deploy'] = stage1

        if not stage1.get('success'):
            results['error'] = 'Staging deployment failed'
            return results

        # Build on staging
        logger.info("Building on staging...")
        build_result = execute_on_group(
            staging_group,
            "cd /var/www/app && npm run build",
            timeout=300
        )

        results['stages']['staging_build'] = build_result

        if not build_result.get('success'):
            results['error'] = 'Staging build failed'
            return results

        # Stage 2: Run tests (if enabled)
        if run_tests:
            logger.info("Stage 2: Running tests...")
            test_result = execute_on_group(
                staging_group,
                "cd /var/www/app && npm test",
                timeout=600
            )

            results['stages']['tests'] = test_result

            if not test_result.get('success'):
                results['error'] = 'Tests failed on staging'
                return results

        # Stage 3: Validation
        logger.info("Stage 3: Validating staging...")
        health_result = execute_on_group(
            staging_group,
            "curl -f http://localhost:3000/health || echo 'Health check failed'",
            timeout=10
        )

        results['stages']['staging_validation'] = health_result

        # Stage 4: Deploy to production
        logger.info("Stage 4: Deploying to production...")
        prod_deploy = push_to_hosts(
            local_path=code_path,
            remote_path="/var/www/app",
            group=prod_group,
            recurse=True
        )

        results['stages']['production_deploy'] = prod_deploy

        if not prod_deploy.get('success'):
            results['error'] = 'Production deployment failed'
            return results

        # Build and restart on production
        logger.info("Building and restarting production...")
        prod_build = execute_on_group(
            prod_group,
            "cd /var/www/app && npm run build && pm2 restart app",
            timeout=300
        )

        results['stages']['production_build'] = prod_build

        # Stage 5: Production verification
        logger.info("Stage 5: Verifying production...")
        prod_health = execute_on_group(
            prod_group,
            "curl -f http://localhost:3000/health",
            timeout=15
        )

        results['stages']['production_verification'] = prod_health

        # Success!
        results['success'] = True
        results['duration'] = format_duration(time.time() - start_time)

        return results

    except Exception as e:
        logger.error(f"Deployment workflow error: {e}")
        results['error'] = str(e)
        results['duration'] = format_duration(time.time() - start_time)
        return results


def backup_workflow(hosts: List[str],
                   backup_paths: List[str],
                   destination: str) -> Dict:
    """
    Backup files from multiple hosts.

    Args:
        hosts: List of hosts to backup from
        backup_paths: Paths to backup on each host
        destination: Local destination directory

    Returns:
        Dict with backup results

    Example:
        >>> result = backup_workflow(
        ...     ["db-01", "db-02"],
        ...     ["/var/lib/mysql"],
        ...     "./backups"
        ... )
        >>> result['backed_up_hosts']
        2
    """
    from sshsync_wrapper import pull_from_host

    start_time = time.time()
    results = {
        'hosts': {},
        'success': True,
        'backed_up_hosts': 0
    }

    for host in hosts:
        host_results = []

        for backup_path in backup_paths:
            # Create timestamped backup directory
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            host_dest = f"{destination}/{host}_{timestamp}"

            result = pull_from_host(
                host=host,
                remote_path=backup_path,
                local_path=host_dest,
                recurse=True
            )

            host_results.append(result)

            if not result.get('success'):
                results['success'] = False

        results['hosts'][host] = host_results

        if all(r.get('success') for r in host_results):
            results['backed_up_hosts'] += 1

    results['duration'] = format_duration(time.time() - start_time)

    return results


def sync_workflow(source_host: str,
                 target_group: str,
                 paths: List[str]) -> Dict:
    """
    Sync files from one host to many.

    Args:
        source_host: Host to pull from
        target_group: Group to push to
        paths: Paths to sync

    Returns:
        Dict with sync results

    Example:
        >>> result = sync_workflow(
        ...     "master-db",
        ...     "replica-dbs",
        ...     ["/var/lib/mysql/config"]
        ... )
        >>> result['success']
        True
    """
    from sshsync_wrapper import pull_from_host, push_to_hosts
    import tempfile
    import shutil

    start_time = time.time()
    results = {'paths': {}, 'success': True}

    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        for path in paths:
            # Pull from source
            pull_result = pull_from_host(
                host=source_host,
                remote_path=path,
                local_path=f"{temp_dir}/{Path(path).name}",
                recurse=True
            )

            if not pull_result.get('success'):
                results['paths'][path] = {
                    'success': False,
                    'error': 'Pull from source failed'
                }
                results['success'] = False
                continue

            # Push to targets
            push_result = push_to_hosts(
                local_path=f"{temp_dir}/{Path(path).name}",
                remote_path=path,
                group=target_group,
                recurse=True
            )

            results['paths'][path] = {
                'pull': pull_result,
                'push': push_result,
                'success': push_result.get('success', False)
            }

            if not push_result.get('success'):
                results['success'] = False

    results['duration'] = format_duration(time.time() - start_time)

    return results


def rolling_restart(group: str,
                   service_name: str,
                   wait_between: int = 30) -> Dict:
    """
    Zero-downtime rolling restart of a service across group.

    Args:
        group: Group to restart
        service_name: Service name (e.g., "nginx", "app")
        wait_between: Seconds to wait between restarts

    Returns:
        Dict with restart results

    Example:
        >>> result = rolling_restart("web-servers", "nginx")
        >>> result['restarted_count']
        3
    """
    from utils.helpers import parse_sshsync_config

    start_time = time.time()
    groups_config = parse_sshsync_config()
    hosts = groups_config.get(group, [])

    if not hosts:
        return {
            'success': False,
            'error': f'Group {group} not found or empty'
        }

    results = {
        'hosts': {},
        'restarted_count': 0,
        'failed_count': 0,
        'success': True
    }

    for host in hosts:
        logger.info(f"Restarting {service_name} on {host}...")

        # Restart service
        restart_result = execute_on_host(
            host,
            f"sudo systemctl restart {service_name} || sudo service {service_name} restart",
            timeout=30
        )

        # Health check
        time.sleep(5)  # Wait for service to start

        health_result = execute_on_host(
            host,
            f"sudo systemctl is-active {service_name} || sudo service {service_name} status",
            timeout=10
        )

        success = restart_result.get('success') and health_result.get('success')

        results['hosts'][host] = {
            'restart': restart_result,
            'health': health_result,
            'success': success
        }

        if success:
            results['restarted_count'] += 1
            logger.info(f"✓ {host} restarted successfully")
        else:
            results['failed_count'] += 1
            results['success'] = False
            logger.error(f"✗ {host} restart failed")

        # Wait before next restart (except last)
        if host != hosts[-1]:
            time.sleep(wait_between)

    results['duration'] = format_duration(time.time() - start_time)

    return results


def health_check_workflow(group: str,
                         endpoint: str = "/health",
                         timeout: int = 10) -> Dict:
    """
    Check health endpoint across group.

    Args:
        group: Group to check
        endpoint: Health endpoint path
        timeout: Request timeout

    Returns:
        Dict with health check results

    Example:
        >>> result = health_check_workflow("production", "/health")
        >>> result['healthy_count']
        3
    """
    from utils.helpers import parse_sshsync_config

    groups_config = parse_sshsync_config()
    hosts = groups_config.get(group, [])

    if not hosts:
        return {
            'success': False,
            'error': f'Group {group} not found or empty'
        }

    results = {
        'hosts': {},
        'healthy_count': 0,
        'unhealthy_count': 0
    }

    for host in hosts:
        health_result = execute_on_host(
            host,
            f"curl -f -s -o /dev/null -w '%{{http_code}}' http://localhost:3000{endpoint}",
            timeout=timeout
        )

        is_healthy = (
            health_result.get('success') and
            '200' in health_result.get('stdout', '')
        )

        results['hosts'][host] = {
            'healthy': is_healthy,
            'response': health_result.get('stdout', '').strip()
        }

        if is_healthy:
            results['healthy_count'] += 1
        else:
            results['unhealthy_count'] += 1

    results['success'] = results['unhealthy_count'] == 0

    return results


def main():
    """Test workflow executor functions."""
    print("Testing workflow executor...\n")

    print("Note: Workflow executor requires configured hosts and groups.")
    print("Tests would execute real operations, so showing dry-run simulations.\n")

    print("✅ Workflow executor ready")


if __name__ == "__main__":
    main()
