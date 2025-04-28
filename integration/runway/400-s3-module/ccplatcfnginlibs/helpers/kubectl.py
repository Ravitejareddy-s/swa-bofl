"""kubectl helper functions."""

from __future__ import annotations

import logging
import shlex
import stat
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from kubernetes import client
from kubernetes.config.kube_config import load_kube_config

if TYPE_CHECKING:
    from _typeshed import StrPath
    from kubernetes.client.models import V1ServiceDict

LOGGER = logging.getLogger(__name__)


def delete_all_client_namespaces() -> None:
    """Delete all client namespaces.

    Raises:
        TimeoutError: If the namespaces do not delete within 5 minutes.

    """
    load_kube_config()

    api_v1 = client.CoreV1Api()
    deleted_namespaces: list[str] = []

    namespaces = api_v1.list_namespace(watch=False).items
    for namespace in namespaces:
        if namespace.metadata:
            namespace_name = namespace.metadata.name
            if namespace_name and namespace_name not in [
                "kube-system",
                "default",
                "kube-node-lease",
                "kube-public",
            ]:
                LOGGER.info("deleting kubernetes namespace: %s", namespace_name)
                api_v1.delete_namespace(name=namespace_name)
                deleted_namespaces.append(namespace_name)

    living_namespaces = api_v1.list_namespace(watch=False).items
    for namespace in living_namespaces:
        if namespace.metadata and namespace.metadata.name in deleted_namespaces:
            wait_for_namespace_delete(namespace.metadata.name)


def fix_permissions(target_dir: StrPath) -> None:
    """Fix permissions of files in directory by ensuring all files are executable.

    Args:
        target_dir: The directory to fix permissions for.

    """
    for child in Path(target_dir).iterdir():
        if child.is_dir():
            fix_permissions(child)
        else:
            child.chmod(child.stat().st_mode | stat.S_IEXEC)


def retrieve_service_config(service_name: str, namespace: str) -> V1ServiceDict | None:
    """Get configuration of a service.

    Args:
        service_name: The name of the service to get configuration for.
        namespace: The namespace the service is in.

    """
    load_kube_config()
    api_v1 = client.CoreV1Api()
    try:
        return api_v1.read_namespaced_service(
            name=service_name, namespace=namespace
        ).to_dict()
    except Exception as exc:
        if "Not Found" in str(exc):
            LOGGER.warning(
                "unable to find service %s in namespace %s", service_name, namespace
            )
        else:
            LOGGER.exception(
                "an error occurred while attempting to retrieve service %s "
                "in namespace %s",
                service_name,
                namespace,
            )
    return None


def setup_kube_ctl(cluster_name: str) -> None:
    """Configure kubectl.

    Args:
        cluster_name: The name of the cluster to configure kubectl for.

    """
    subprocess.check_call(  # noqa: S602
        shlex.join(["bash", "-c", f"k8s/scripts/setup_kube_ctl.sh {cluster_name}"]),
        shell=True,
    )


def wait_for_namespace_delete(namespace_wait: str) -> None:
    """Wait for a given namespace to delete.

    Args:
        namespace_wait: The namespace to wait for deletion.

    Raises:
        TimeoutError: If the namespace does not delete within 5 minutes.

    """
    load_kube_config()
    api_v1 = client.CoreV1Api()
    wait = True
    sleep_time = 5
    sleep_incrementor = 2
    while wait:
        wait = False
        living_namespaces = api_v1.list_namespace(watch=False).items
        for namespace in living_namespaces:
            if namespace.metadata and namespace.metadata.name == namespace_wait:
                wait = True
                if sleep_time > 300:
                    raise TimeoutError("TIMEOUT WAITING FOR NAMESPACES TO DELETE")
                LOGGER.info(
                    "namespace %s is still alive; waiting %s...",
                    namespace.metadata.name,
                    sleep_time,
                )
                time.sleep(sleep_time)
                sleep_time = sleep_time * sleep_incrementor
