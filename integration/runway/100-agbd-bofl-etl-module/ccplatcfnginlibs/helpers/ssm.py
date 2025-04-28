"""SSM helper functions.

These are here because CFN doesn't allow for encrypted parameters.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import boto3
from botocore.config import Config
from deprecated import deprecated

from . import cloudformation

if TYPE_CHECKING:
    from mypy_boto3_ssm.client import SSMClient
    from mypy_boto3_ssm.type_defs import ParameterTypeDef


@deprecated(reason="use delete_parameter directly")
def delete_parameter(name: str) -> None:
    """Delete parameter.

    Args:
        name: Name of the parameter to delete.

    """
    get_ssm_client().delete_parameter(Name=name)


@deprecated(reason="use delete_parameters directly")
def delete_parameters(parameters: list[str], region: str | None = None) -> None:
    """Delete parameters.

    Args:
        parameters: List of parameters to delete.
        region: AWS region.

    """
    client = get_ssm_client(region)
    for chunk in [
        parameters[i * 10 : (i + 1) * 10]
        for i in range((len(parameters) + 10 - 1) // 10)
    ]:
        client.delete_parameters(Names=chunk)


# TODO(kyle): remove this - it is more harmful than helpful
@deprecated(reason="boto3 sessions should be created from CFNgin's context object")
def get_ssm_client(region: str | None = None) -> SSMClient:  # cov: ignore
    """boto3 client for ssm."""
    return boto3.Session().client(
        "ssm", config=Config(retries={"max_attempts": 20}), region_name=region
    )


@deprecated(reason="use CFNgin's provider object or 'cfn' lookup instead")
def get_kms_key() -> str:
    """Get KMS Key to use for SSM secure string.

    This is here for unit testing.

    """
    return cloudformation.get_output("EC-KmsKey", "KmsKeyID")


@deprecated(
    reason="reference CloudFormation outputs directly instead of using SSM "
    "parameters created from the outputs"
)
def get_module_parameters(
    path: str, region: str | None = None
) -> list[ParameterTypeDef]:
    """Get module parameters.

    Args:
        path: SSM Parameter Path.
        region: AWS region.

    """
    return [
        param
        for page in get_ssm_client(region)
        .get_paginator("get_parameters_by_path")
        .paginate(Path=path, Recursive=True, WithDecryption=True)
        for param in page["Parameters"]
    ]


@deprecated(reason="use CFNgin's 'ssm' lookup instead or use get_parameter directly")
def get_parameter(parameter: str, region: str | None = None) -> str | None:
    """Retrieve parameter.

    Args:
        parameter: Parameter to retrieve.
        region: AWS region.

    """
    return (
        get_ssm_client(region)
        .get_parameter(Name=parameter, WithDecryption=True)["Parameter"]
        .get("Value")
    )


@deprecated(
    reason="reference CloudFormation outputs directly instead of using SSM "
    "parameters created from the outputs"
)
def get_stack_outputs(
    stack_resource_name: str, stack_name: str, namespace: str
) -> dict[str, str | None]:
    """Get SSM parameters based on provided stack resource, stack name and namespace.

    Args:
        stack_resource_name: Name of the stack resource.
        stack_name: Name of the stack.
        namespace: Namespace of the parameter.

    """
    return {
        param.get("Name", "").split("/")[-1]: param.get("Value")
        for param in get_module_parameters(
            f"/ccplat/{namespace}/cloud-common-{stack_resource_name}-module/{stack_name}"
        )
    }


@deprecated(
    reason="reference CloudFormation outputs directly instead of using SSM "
    "parameters created from the outputs"
)
def get_stack_parameter(
    stack_resource_name: str, stack_name: str, parameter: str, namespace: str
) -> str | None:
    """Get SSM parameter based on provided stack resource, stack name, param name and namespace.

    Args:
        stack_resource_name: Name of the stack resource.
        stack_name: Name of the stack.
        parameter: Name of the parameter.
        namespace: Namespace of the parameter.

    """
    return get_parameter(
        f"/ccplat/{namespace}/cloud-common-{stack_resource_name}-module/{stack_name}/{parameter}"
    )


@deprecated(reason="use put_parameter & add_tags_to_resource directly")
def put_secure_string_parameter(
    name: str, value: str, description: str, tag_dict: dict[str, str]
) -> None:
    """Write a secure string parameter.

    Args:
        name: SSM Parameter Name.
        value: SSM Parameter Value.
        description: SSM Parameter Description.
        tag_dict: Dictionary of Tags.

    """
    client = get_ssm_client()
    client.put_parameter(
        Description=description,
        KeyId=get_kms_key(),
        Name=name,
        Overwrite=True,
        Type="SecureString",
        Value=value,
    )
    client.add_tags_to_resource(
        ResourceId=name,
        ResourceType="Parameter",
        Tags=[{"Key": k, "Value": v} for k, v in tag_dict.items()],
    )


@deprecated(reason="use put_parameter & add_tags_to_resource directly")
def put_string_parameter(
    name: str,
    value: Any,
    description: str,
    tag_dict: dict[str, str],
    region: str | None = None,
) -> None:
    """Write a secure string parameter.

    Args:
        name: SSM Parameter Name.
        value: SSM Parameter Value.
        description: SSM Parameter Description.
        tag_dict: Dictionary of Tags.
        region: AWS region.

    """
    client = get_ssm_client(region)
    client.put_parameter(
        Name=name, Description=description, Value=value, Type="String", Overwrite=True
    )
    client.add_tags_to_resource(
        ResourceType="Parameter",
        ResourceId=name,
        Tags=[{"Key": k, "Value": v} for k, v in tag_dict.items()],
    )
