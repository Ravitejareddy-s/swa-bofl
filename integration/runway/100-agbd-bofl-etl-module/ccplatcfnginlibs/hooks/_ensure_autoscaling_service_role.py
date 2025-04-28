"""Ensure the AutoScaling Service Role exists & has KMS Key grant.

:Path: ``ccplatcfnginlibs.hooks.ensure_autoscaling_service_role``

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..constants import KMS_KEY_GRANT_OPERATIONS, KMS_KEY_IDS

if TYPE_CHECKING:
    from runway.context import CfnginContext

AWS_SERVICE_NAME = "autoscaling.amazonaws.com"
"""AWS service name used to create the service role."""

ROLE_NAME = "AWSServiceRoleForAutoScaling"
"""Name of the service role."""


def ensure_autoscaling_service_role(
    context: CfnginContext, *__args: Any, **__kwargs: Any
) -> str:
    """Ensure the AutoScaling Service Role exists & has KMS Key grant.

    Args:
        context: CFNgin context object.

    Returns:
        ARN of service role.

    """
    session = context.get_session()
    iam_client = session.client("iam")
    try:
        role_arn = iam_client.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
    except iam_client.exceptions.NoSuchEntityException:
        role_arn = iam_client.create_service_linked_role(
            AWSServiceName=AWS_SERVICE_NAME
        )["Role"]["Arn"]

    kms_client = session.client("kms")
    if not [
        i
        for page in kms_client.get_paginator("list_grants").paginate(
            GranteePrincipal=role_arn, KeyId=KMS_KEY_IDS[context.env.aws_region]
        )
        for i in page["Grants"]
    ]:
        session.client("kms").create_grant(
            KeyId=KMS_KEY_IDS[context.env.aws_region],
            GranteePrincipal=role_arn,
            Operations=KMS_KEY_GRANT_OPERATIONS,
        )
    return role_arn
