"""Route53 helper functions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import boto3
from deprecated import deprecated

if TYPE_CHECKING:
    from mypy_boto3_route53.client import Route53Client
    from mypy_boto3_route53.type_defs import (
        ChangeTypeDef,
        ResourceRecordSetOutputTypeDef,
    )

LOGGER = logging.getLogger(__name__)


# TODO(kyle): remove this - it is more harmful than helpful
@deprecated(reason="boto3 sessions should be created from CFNgin's context object")
def get_r53_client() -> Route53Client:  # pragma: no cover
    """boto3 client for route53.

    This is here for unit testing.

    """
    return boto3.Session().client("route53")


def delete_all_orphans(hosted_zone: str) -> list[ChangeTypeDef]:
    """Delete orphans.

    Args:
        hosted_zone: The hosted zone to delete orphans from.

    Returns:
        List of changes that were applied.

    """
    route53 = get_r53_client()
    changes: list[ChangeTypeDef] = [
        cast("ChangeTypeDef", {"Action": "DELETE", "ResourceRecordSet": record})
        for record in get_all_orphans(route53, hosted_zone)
    ]
    if len(changes) != 0:
        LOGGER.info("deleting orphans from hosted zone %s...", hosted_zone)
        LOGGER.info("applying changes:\n%s", changes)
        route53.change_resource_record_sets(
            HostedZoneId=hosted_zone, ChangeBatch={"Changes": changes}
        )
    return changes


@deprecated(reason="this has been implemented in the EKS module")
def delete_k8s_external_dns_orphans(
    hosted_zone: str, region: str
) -> list[ChangeTypeDef]:
    """Delete orphans.

    Args:
        hosted_zone: The hosted zone to delete orphans from.
        region: The region to delete orphans from.

    Returns:
        List of changes that were applied.

    """
    route53 = get_r53_client()
    changes: list[ChangeTypeDef] = [
        cast("ChangeTypeDef", {"Action": "DELETE", "ResourceRecordSet": record})
        for record in get_k8s_external_dns_orphans(route53, hosted_zone, region)
    ]
    if len(changes) != 0:
        LOGGER.info("deleting orphans from hosted zone %s...", hosted_zone)
        LOGGER.info("applying changes:\n%s", changes)
        route53.change_resource_record_sets(
            HostedZoneId=hosted_zone, ChangeBatch={"Changes": changes}
        )
    return changes


def get_all_orphans(
    route53: Route53Client, hosted_zone: str
) -> list[ResourceRecordSetOutputTypeDef]:
    """Get orphans.

    Args:
        route53: The boto3 route53 client.
        hosted_zone: The hosted zone to get orphans from.

    Returns:
        List of orphans.

    """
    return [
        resource_record_set
        for page in route53.get_paginator("list_resource_record_sets").paginate(
            HostedZoneId=hosted_zone
        )
        for resource_record_set in page["ResourceRecordSets"]
        if resource_record_set["Type"] not in ["NS", "SOA"]
    ]


def get_hz_id(hz_name: str) -> str | None:
    """Get ID of hosted zone.

    Args:
        hz_name: The hosted zone name to get ID for.

    Returns:
        The hosted zone ID.

    """
    for hzone in get_r53_client().list_hosted_zones_by_name(DNSName=hz_name)[
        "HostedZones"
    ]:
        if hzone["Name"] == hz_name:
            return hzone["Id"].split("/")[2]
    LOGGER.error("unable to get ID for hosted zone %s", hz_name)
    return None


def get_hz_region(hz_id: str) -> str:
    """Get hosted zone's region based on CCP:Region tag."""
    return next(
        tag
        for tag in get_r53_client()
        .list_tags_for_resource(ResourceType="hostedzone", ResourceId=hz_id)[
            "ResourceTagSet"
        ]
        .get("Tags", [])
        if tag.get("Key") == "CCP:Region" and "Value" in tag
    )["Value"]


def get_k8s_external_dns_orphans(
    route53: Route53Client, hosted_zone: str, region: str
) -> list[ResourceRecordSetOutputTypeDef]:
    """Get orphans.

    Args:
        route53: The boto3 route53 client.
        hosted_zone: The hosted zone to get orphans from.
        region: The region to get orphans from.

    """
    record_sets = [
        resource_record_set
        for page in route53.get_paginator("list_resource_record_sets").paginate(
            HostedZoneId=hosted_zone
        )
        for resource_record_set in page["ResourceRecordSets"]
    ]
    external_dns_record_names: set[str] = set()
    for i in record_sets:
        if i["Type"] == "TXT":
            for record in i.get("ResourceRecords", []):
                if "Value" in record and "external-dns" in record["Value"]:
                    external_dns_record_names.add(i["Name"])
    LOGGER.info("external_dns_record_names: %s", external_dns_record_names)
    return [
        i
        for i in record_sets
        if i["Name"] in external_dns_record_names
        and region in i.get("SetIdentifier", "")
    ]
