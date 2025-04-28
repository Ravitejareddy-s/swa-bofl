"""STS helper functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import boto3
from deprecated import deprecated

if TYPE_CHECKING:
    from mypy_boto3_sts.client import STSClient


# TODO(kyle): remove this - it is more harmful than helpful
@deprecated(reason="boto3 sessions should be created from CFNgin's context object")
def get_sts_client() -> STSClient:  # cov: ignore
    """boto3 client for sts."""
    return boto3.client("sts")


@deprecated(reason="use get_caller_identity directly")
def get_account_id() -> str:
    """Get account ID."""
    return get_sts_client().get_caller_identity()["Account"]
