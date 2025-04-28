"""CloudWatch helper functions."""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

import boto3
from deprecated import deprecated

if TYPE_CHECKING:
    from mypy_boto3_logs.client import CloudWatchLogsClient


class EnvironmetLogRetention(IntEnum):
    """Log retention in days by environment tier."""

    LAB = 1
    DEV = 5
    QA = 30
    PROD = 90


# TODO(kyle): remove this - it is more harmful than helpful
@deprecated(reason="boto3 sessions should be created from CFNgin's context object")
def get_logs_client() -> CloudWatchLogsClient:  # cov: ignore
    """boto3 client for logs."""
    return boto3.client("logs")


@deprecated(reason="use EnvironmetLogRetention instead")
def get_log_retention_setting(env: str) -> int:
    """Get log retention.

    Args:
        env: Environment.

    Returns:
        Log retention in days.

    """
    return EnvironmetLogRetention[env.upper()].value


@deprecated(reason="use put_retention_policy directly")
def set_log_retention(log_group: str, env: str) -> int:
    """Set log retention.

    Args:
        log_group: Name of the log group.
        env: Environment.

    Returns:
        Log retention in days.

    """
    retention_days = EnvironmetLogRetention[env.upper()].value
    get_logs_client().put_retention_policy(
        logGroupName=log_group, retentionInDays=retention_days
    )
    return retention_days
