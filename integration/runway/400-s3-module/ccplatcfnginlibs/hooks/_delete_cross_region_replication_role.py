"""Delete Role for Cross Region Replication.

:Path: ``ccplatcfnginlibs.hooks.delete_cross_region_replication_role``

.. rubric:: Example
.. code-block:: yaml

  pre_destroy:
    - path: ccplatcfnginlibs.hooks.delete_cross_region_replication_role
      args:
        department: ${department}
        module_config_path: ${module_config}

"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml
from pydantic import Field
from runway.utils import BaseModel

if TYPE_CHECKING:
    from _typeshed import StrPath
    from mypy_boto3_iam import IAMClient
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


class CrossRegionReplicationModel(BaseModel):
    """Cross Region Replication data model."""

    # Destination cross region replication params
    destination_bucket_region: Optional[str] = Field(
        default=None, alias="destinationRegion"
    )
    """Region that destination bucket lives in."""

    destination_bucket_name: Optional[str] = Field(
        default=None, alias="destinationFullBucketName"
    )
    """Full destination bucket name."""


class BucketConfigDataModel(BaseModel):
    """Bucket configuration data model."""

    name: str
    """Name of the bucket."""

    cross_region_replication: Optional[list[CrossRegionReplicationModel]] = Field(
        default=[], alias="crossRegionReplication"
    )
    """Cross Region replication configurations."""


class ModuleConfigDataModel(BaseModel):
    """Module configuration data model."""

    bucket_list: list[BucketConfigDataModel] = Field(default=[], alias="vBucketList")
    """List of buckets to configure."""


def delete_crr_policy(
    client: IAMClient,
    role_name: str,
) -> bool:
    """Deletes cross region replication policies associated with role name."""
    try:
        response = client.list_attached_role_policies(RoleName=role_name)
        for policy in response["AttachedPolicies"]:
            if (
                "s3crr_kms_for_" in policy.get("PolicyName", "")
                and "PolicyArn" in policy
            ):
                client.detach_role_policy(
                    RoleName=role_name, PolicyArn=policy["PolicyArn"]
                )
                client.delete_policy(PolicyArn=policy["PolicyArn"])
        return True
    except client.exceptions.NoSuchEntityException:
        LOGGER.info("No policies found.")
        return False


def delete_crr_role(client: IAMClient, role_name: str) -> bool:
    """Deletes cross region replication roles."""
    try:
        LOGGER.info("Removing IAM role %s...", role_name)
        if delete_crr_policy(client=client, role_name=role_name):
            client.delete_role(RoleName=role_name)
    except client.exceptions.NoSuchEntityException:
        LOGGER.info("skipped removing role; %s doesn't exists", role_name)
    return False


def delete_cross_region_replication_role(
    context: CfnginContext,
    *__args: Any,
    department: str,
    module_config_path: StrPath,
    **__kwargs: Any,
) -> bool:
    """Delete IAM role for CRR."""
    bucket_list = ModuleConfigDataModel.model_validate(
        yaml.safe_load(Path(module_config_path).read_bytes())
    ).bucket_list
    session = context.get_session()
    client = session.client("iam")

    # Build the names of replication source buckets
    bucket_names_source = {
        (
            rule.destination_bucket_name
            or f"{department}-{rule.destination_bucket_region}-{context.namespace}-{bucket.name}"
        )
        for bucket in bucket_list
        if bucket.cross_region_replication
        for rule in bucket.cross_region_replication
    }

    # Build the names of replication destination buckets.
    bucket_names_destination = {
        f"{department}-{session.region_name}-{context.namespace}-{bucket.name}"
        for bucket in bucket_list
        if bucket.cross_region_replication
    }

    for bucket in bucket_names_source:
        role_name = f"s3crr_role_for_{bucket}"[0:63]
        delete_crr_role(client=client, role_name=role_name)

    for bucket in bucket_names_destination:
        role_name = f"s3crr_role_for_{bucket}"[0:63]
        delete_crr_role(client=client, role_name=role_name)

    return True
