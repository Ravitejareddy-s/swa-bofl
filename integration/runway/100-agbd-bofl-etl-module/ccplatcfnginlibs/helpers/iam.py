"""IAM helper functions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError
from deprecated import deprecated

if TYPE_CHECKING:
    from mypy_boto3_iam.client import IAMClient

SERVICE_ROLE_NAMES: dict[str, str] = {
    "autoscaling": "AWSServiceRoleForAutoScaling",
    "dynamodb.application-autoscaling": "AWSServiceRoleForApplicationAutoScaling_DynamoDBTable",
    "ops.apigateway": "AWSServiceRoleForAPIGateway",
}

LOGGER = logging.getLogger(__name__)


# TODO(kyle): remove this - it is more harmful than helpful
@deprecated(reason="boto3 sessions should be created from CFNgin's context object")
def get_iam_client(region: str | None = None) -> IAMClient:  # cov: ignore
    """Return the IAM client."""
    return boto3.client("iam", region_name=region)


@deprecated(reason="use get_role directly")
def get_service_role_arn(
    role_name: str, region: str | None = None
) -> str | None:  # cov: ignore
    """Return the service role arn for the role_name if exists or ``None`` if not."""
    try:
        return get_iam_client(region).get_role(RoleName=role_name)["Role"]["Arn"]
    except ClientError:
        LOGGER.exception("unable to find service role for %s", role_name)
    return None


def create_api_gateway_service_role(region: str | None = None) -> str | None:
    """Create the API Gateway service role.

    Args:
        region: AWS region.

    Returns:
        ARN of service role.

    """
    return create_service_role("ops.apigateway", region)


def create_autoscaling_service_role(region: str | None = None) -> str:
    """Create the Autoscaling service role.

    Args:
        region: AWS region.

    Returns:
        ARN of service role.

    """
    return create_service_role("autoscaling", region)


def create_ddb_app_autoscaling_service_role(
    region: str | None = None,
) -> str | None:
    """Create the DynamoDB Application Autoscaling service role.

    Args:
        region: AWS region.

    Returns:
        ARN of service role.

    """
    return create_service_role("dynamodb.application-autoscaling", region)


@deprecated(reason="use create_service_linked_role directly")
def create_service_role(service_prefix: str, region: str | None = None) -> str:
    """Determine if service role exists using role_name.

    Args:
        service_prefix: The service prefix.
        region: AWS region.

    Returns:
        ARN of service role if successful, None if unsuccessful.

    """
    client = get_iam_client(region)
    try:
        role_arn = client.get_role(RoleName=SERVICE_ROLE_NAMES[service_prefix])["Role"][
            "Arn"
        ]
    except ClientError:
        role_arn = client.create_service_linked_role(
            AWSServiceName=f"{service_prefix}.amazonaws.com"
        )["Role"]["Arn"]
        LOGGER.info("service linked role created: %s", role_arn)
    return role_arn
