"""Cloudformation helper functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from deprecated import deprecated

if TYPE_CHECKING:
    from mypy_boto3_cloudformation.client import CloudFormationClient
    from mypy_boto3_cloudformation.type_defs import OutputTypeDef


# TODO(kyle): remove this - it is more harmful than helpful
@deprecated(reason="boto3 sessions should be created from CFNgin's context object")
def get_cfn_client(
    region: str | None = None,
) -> CloudFormationClient:  # cov: ignore
    """boto3 client for CloudFormation.

    Args:
        region: AWS region.

    """
    return boto3.Session().client(
        "cloudformation",
        config=Config(retries={"max_attempts": 20}),
        region_name=region,
    )


@deprecated(reason="use CFNgin's provider object instead")
def get_all_outputs(stack: str) -> list[OutputTypeDef]:
    """Get all outputs from stack.

    Args:
        stack: Name of the stack.

    Raises:
        ClientError: If the stack does not exist.

    """
    return (
        get_cfn_client()
        .describe_stacks(StackName=stack)["Stacks"][0]
        .get("Outputs", [])
    )


@deprecated(reason="use CFNgin's provider object or 'cfn' lookup instead")
def get_kms_key_id(
    account_id: str, region: str, session: boto3.Session | None = None
) -> str:
    """Get KMS key ID.

    Args:
        account_id: AWS account ID.
        region: AWS region.
        session: boto3 session.

    Raises:
        Exception: If the key is not found.

    """
    client = session.client("cloudformation") if session else get_cfn_client(region)
    matches = [
        export
        for export in client.list_exports()["Exports"]
        if export.get("Name") == f"{account_id}-{region}-swa-kms-key-arn"
    ]
    if not matches:
        raise ValueError("Could not find SWA KMS Key ID")
    return matches[0].get("Value", "")


@deprecated(reason="use CFNgin's provider object or 'cfn' lookup instead")
def get_output(stack: str, desired_output: str) -> str:
    """Get output from stack.

    Args:
        stack: Name of the stack.
        desired_output: Name of the output.

    Raises:
        ValueError: If the output is not found.

    """
    for output in get_all_outputs(stack):
        if output.get("OutputKey", "").upper() == desired_output.upper():
            return output.get("OutputValue", "")
    raise ValueError(f"output {desired_output} not found for stack {stack}")


@deprecated(reason="use CFNgin's provider instead")
def stack_exists(name: str) -> bool:
    """Check stack exists.

    Args:
        name: Name of the stack.

    Returns:
        True if the stack exists, False otherwise.

    """
    try:
        get_cfn_client().describe_stacks(StackName=name)
    except ClientError:
        return False
    return True
