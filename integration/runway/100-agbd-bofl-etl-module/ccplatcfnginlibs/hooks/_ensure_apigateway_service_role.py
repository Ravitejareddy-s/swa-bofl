"""Ensure the API Gateway Service Role exists.

:Path: ``ccplatcfnginlibs.hooks.ensure_apigateway_service_role``

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from runway.context import CfnginContext


AWS_SERVICE_NAME = "ops.apigateway.amazonaws.com"
"""AWS service name used to create the service role."""

ROLE_NAME = "AWSServiceRoleForAPIGateway"
"""Name of the service role."""


def ensure_apigateway_service_role(
    context: CfnginContext, *__args: Any, **__kwargs: Any
) -> str:
    """Ensure the API Gateway Service Role exists.

    Args:
        context: CFNgin context object.

    Returns:
        ARN of service role.

    """
    client = context.get_session().client("iam")
    try:
        return client.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
    except client.exceptions.NoSuchEntityException:
        return client.create_service_linked_role(AWSServiceName=AWS_SERVICE_NAME)[
            "Role"
        ]["Arn"]
