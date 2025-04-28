"""KMS helper functions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError
from deprecated import deprecated

if TYPE_CHECKING:
    from mypy_boto3_kms.client import KMSClient

LOGGER = logging.getLogger(__name__)

GRANT_OPERATIONS = (
    "CreateGrant",
    "Decrypt",
    "DescribeKey",
    "Encrypt",
    "GenerateDataKey",
    "GenerateDataKeyWithoutPlaintext",
    "ReEncryptFrom",
    "ReEncryptTo",
)


# TODO(kyle): remove this - it is more harmful than helpful
@deprecated(reason="boto3 sessions should be created from CFNgin's context object")
def get_kms_client(region: str | None = None) -> KMSClient:  # cov: ignore
    """Return the KMS client."""
    return boto3.client("kms", region_name=region)


@deprecated(reason="call create_grant directly")
def create_grant(kms_key_id: str, role_arn: str, region: str | None = None) -> bool:
    """Create a grant for the passed KMS key and role.

    Args:
        kms_key_id: The KMS key ID.
        role_arn: The role ARN.
        region: AWS region.

    Returns:
        False if unsuccessful.

    """
    try:
        get_kms_client(region).create_grant(
            KeyId=kms_key_id,
            GranteePrincipal=role_arn,
            Operations=GRANT_OPERATIONS,
        )
        LOGGER.info("grant created for key %s and role %s", kms_key_id, role_arn)
    except ClientError:
        LOGGER.exception(
            "Unable to create grant for key %s and role %s", kms_key_id, role_arn
        )
        return False
    return True


def grant_exists_for_role(
    kms_key_id: str, role_arn: str, region: str | None = None
) -> bool:
    """Determine if the grant for an IAM Role exists.

    Args:
        kms_key_id: The KMS key ID.
        role_arn: The role ARN.
        region: AWS region.

    """
    return bool(
        [
            i
            for page in get_kms_client(region)
            .get_paginator("list_grants")
            .paginate(GranteePrincipal=role_arn, KeyId=kms_key_id)
            for i in page["Grants"]
        ]
    )
