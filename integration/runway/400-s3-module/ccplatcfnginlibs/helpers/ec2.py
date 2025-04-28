"""EC2 helper functions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import boto3
from deprecated import deprecated

if TYPE_CHECKING:
    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_ec2.type_defs import NetworkInterfaceTypeDef

LOGGER = logging.getLogger(__name__)


# TODO(kyle): remove this - it is more harmful than helpful
@deprecated(reason="boto3 sessions should be created from CFNgin's context object")
def get_ec2_client() -> EC2Client:  # cov: ignore
    """boto3 client for ec2."""
    return boto3.client("ec2")


def delete_eni_orphans(vpc_id: str) -> list[NetworkInterfaceTypeDef]:
    """Delete orphaned ENIs.

    Args:
        vpc_id: VPC ID.

    Returns:
        List of deleted ENI IDs.

    """
    ec2 = get_ec2_client()
    LOGGER.info("going through ENIs in VPC %s to delete orphans...", vpc_id)
    paginator = ec2.get_paginator("describe_network_interfaces")
    eni_orphans = [
        eni
        for page in paginator.paginate(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )
        for eni in page["NetworkInterfaces"]
        if eni.get("VpcId") == vpc_id
    ]
    for eni in eni_orphans:
        if "NetworkInterfaceId" in eni:
            ec2.delete_network_interface(NetworkInterfaceId=eni["NetworkInterfaceId"])
            LOGGER.info("Deleted ENI orphan: %s", eni["NetworkInterfaceId"])
    return eni_orphans
