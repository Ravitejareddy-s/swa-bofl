"""Configure source and destination buckets for cross region replication.

:Path: ``ccplatcfnginlibs.hooks.configure_cross_region_replication``

.. rubric:: Example
.. code-block:: yaml

  post_deploy:
    - path: ccplatcfnginlibs.hooks.configure_cross_region_replication
      args:
        department: ec
        module_config_path: ${module_config}

"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import awacs.kms
import awacs.s3
import awacs.sts
import yaml
from awacs.aws import (
    Allow,
    Condition,
    PolicyDocument,
    Statement,
    StringLike,
    StringLikeIfExists,
)
from awacs.helpers.trust import make_simple_assume_policy
from pydantic import Field
from runway.core.providers.aws.type_defs import TagTypeDef
from runway.utils import BaseModel

from ..helpers.cloudformation import get_kms_key_id
from ._delete_cross_region_replication_role import delete_cross_region_replication_role

if TYPE_CHECKING:
    import boto3
    from _typeshed import StrPath
    from mypy_boto3_iam import IAMClient
    from mypy_boto3_s3.type_defs import ReplicationRuleOutputTypeDef
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


class CrossRegionReplicationModel(BaseModel):
    """Cross region replication configuration."""

    source_or_destination: str = Field(alias="enableAsDestinationOrSource")
    """Enable replication as source or destination."""

    # List of required params when bucket is enabled as destination type.
    source_bucket_name: Optional[str] = Field(default=None, alias="sourceBucketName")
    """Name of the source bucket."""

    source_bucket_region: Optional[str] = Field(
        default=None, alias="sourceBucketRegion"
    )
    """Region where source bucket lives."""

    # List of required params when bucket is enabled as source type.
    rule_name: Optional[str] = Field(default=None, alias="ruleName")
    """Name of replication rule."""

    destination_full_bucket_name: Optional[str] = Field(
        default=None, alias="destinationFullBucketName"
    )
    """Full name for destination bucket."""

    destination_region: Optional[str] = Field(default=None, alias="destinationRegion")
    """Region of destination bucket."""

    destination_key_ssm: Optional[str] = Field(default=None, alias="destinationKeySsm")
    """Name of SSM param that holds KMS arn of destination bucket."""

    destination_filter_prefix: Optional[str] = Field(
        default=None, alias="destinationS3FilterPrefix"
    )
    """Filter prefix for replication."""

    # List of optional params when bucket is enabled as source type.
    delete_marker_replication: Optional[bool] = Field(
        default=False, alias="deleteMarkerReplication"
    )
    """Delete marker replication flag."""

    disable_bidirectional_replication: Optional[bool] = Field(
        default=True, alias="disableBidirectionalReplication"
    )
    """Disable bidirectional cross-region replication flag."""

    replica_modifications: Optional[bool] = Field(
        default=False, alias="replicaModifications"
    )
    """Replica modifications flag."""


class BucketConfigDataModel(BaseModel):
    """Bucket configuration data model."""

    name: str
    """Name of the bucket."""
    cross_region_replication: Optional[list[CrossRegionReplicationModel]] = Field(
        default=[], alias="crossRegionReplication"
    )
    """Cross Region Replication configuration."""


class ModuleConfigDataModel(BaseModel):
    """Module configuration data model."""

    bucket_list: list[BucketConfigDataModel] = Field(default=[], alias="vBucketList")
    """List of buckets to configure."""


def configure_cross_region_replication(
    context: CfnginContext,
    *__args: Any,
    department: str,
    module_config_path: StrPath,
    **__kwargs: Any,
) -> bool:
    """Configure source and destination buckets for cross region replication."""
    bucket_list = ModuleConfigDataModel.model_validate(
        yaml.safe_load(Path(module_config_path).read_bytes())
    ).bucket_list

    session = context.get_session()
    account_id = session.client("sts").get_caller_identity()["Account"]
    existing_buckets = [
        bucket["Name"]
        for bucket in session.client("s3").list_buckets()["Buckets"]
        if "Name" in bucket
    ]
    tags = [TagTypeDef(Key=k, Value=v) for k, v in context.tags.items()]
    for bucket in bucket_list:  # pylint: disable=not-an-iterable
        source_bucket = (
            f"{department}-{context.env.aws_region}-"
            f"{context.namespace}-{bucket.name}"
        )

        if bucket.cross_region_replication:
            for rule in bucket.cross_region_replication:
                dest_bucket = (
                    rule.destination_full_bucket_name
                    or f"{department}-{rule.destination_region}-{context.namespace}-{bucket.name}"
                )

                if (
                    rule.disable_bidirectional_replication is False
                    and rule.source_or_destination == "source"
                ):
                    destination_region = rule.get("destination_region")
                    source_bucket = (
                        f"{department}-{context.env.aws_region}-"
                        f"{context.namespace}-{bucket.name}"
                    )
                    dest_bucket = (
                        rule.get("destination_full_bucket_name", None)
                        or f"{department}-{destination_region}-{context.namespace}-{bucket.name}"
                    )
                    if (
                        source_bucket in existing_buckets
                        and dest_bucket in existing_buckets
                    ):
                        source_kms_key = get_bucket_kms_key_id(
                            account_id=account_id,
                            region=context.env.aws_region,
                            bucket_name=source_bucket,
                            session=session,
                        )
                        dest_kms_key = get_bucket_kms_key_id(
                            account_id=account_id,
                            region=destination_region,
                            bucket_name=dest_bucket,
                            session=context.get_session(region=destination_region),
                        )
                        configure_rule(
                            session,
                            account_id=account_id,
                            replica_modifications=rule.get("replica_modifications"),
                            delete_marker_replication=rule.get(
                                "delete_marker_replication"
                            ),
                            dest_bucket=source_bucket,
                            dest_kms_key=source_kms_key,
                            dest_region=context.env.aws_region,
                            source_bucket=dest_bucket,
                            source_kms_key=dest_kms_key,
                            source_region=rule.get("destination_region"),
                            prefix_filter=rule.get("destination_filter_prefix"),
                            tags=tags,
                        )
                elif (
                    rule.disable_bidirectional_replication is True
                    and rule.source_or_destination == "source"
                ):
                    remove_replication(
                        source_bucket=dest_bucket,
                        context=context,
                        department=department,
                        module_config_path=module_config_path,
                    )

    return True


def configure_rule(
    session: boto3.Session,
    *,
    account_id: str,
    replica_modifications: bool,
    delete_marker_replication: bool,
    dest_bucket: str,
    dest_kms_key: str,
    dest_region: str,
    source_bucket: str,
    source_kms_key: str,
    source_region: str,
    prefix_filter: str | None = None,
    tags: list[TagTypeDef],
) -> None:
    """Add replication rule to source bucket.

    Args:
        session: boto3 session.
        account_id: AWS account ID.
        replica_modifications: Replica modifications flag.
        delete_marker_replication: Delete marker replication flag.
        dest_bucket: Destination bucket name.
        dest_kms_key: Destination bucket KMS key ARN.
        dest_region: Destination bucket region.
        source_bucket: Source bucket name.
        source_kms_key: Source bucket KMS key ARN.
        source_region: Source bucket region.
        prefix_filter: Prefix filter for replication.
        tags: Tags to apply to resources.

    """
    iam_client = session.client("iam")
    s3_client = session.client("s3")

    role_name = create_role_for_cross_region_replication(
        iam_client, account_id=account_id, bucket_name=source_bucket, tags=tags
    )
    iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn=f"arn:aws:iam::{account_id}:policy/"
        + create_policy_for_cross_region_replication(
            iam_client,
            dest_bucket=dest_bucket,
            dest_kms_key=dest_kms_key,
            dest_region=dest_region,
            source_bucket=source_bucket,
            source_kms_key=source_kms_key,
            source_region=source_region,
        ),
    )

    cross_region_replication_rule: ReplicationRuleOutputTypeDef = {
        # enable rule
        "Status": "Enabled",
        # without specification of Filter, S3 assumes earlier version (V1)
        # we want latest version of schema
        "Filter": {"Prefix": prefix_filter} if prefix_filter else {},
        # enabled replication of kms encrypted objects
        "SourceSelectionCriteria": {
            "SseKmsEncryptedObjects": {"Status": "Enabled"},
            "ReplicaModifications": {
                "Status": ("Enabled" if replica_modifications else "Disabled"),
            },
        },
        # replicating deletes is disabled by default
        "DeleteMarkerReplication": {
            "Status": "Enabled" if delete_marker_replication else "Disabled"
        },
        # specifies replication destination
        "Destination": {
            # kms key used for encrypted objects in destination
            "EncryptionConfiguration": {"ReplicaKmsKeyID": dest_kms_key},
            "Bucket": f"arn:aws:s3:::{dest_bucket}",
            # enable replication time control
            "ReplicationTime": {
                "Status": "Enabled",
                # currently, the only valid value of minutes is 15
                "Time": {"Minutes": 15},
            },
            # if rtc is enabled, metrics must also be specified
            "Metrics": {
                "Status": "Enabled",
                # currently, the only valid value of minutes is 15
                "EventThreshold": {"Minutes": 15},
            },
        },
        "Priority": 1,
        "ID": f"{source_bucket}-cross-region-replication",
    }

    LOGGER.info("Creating bidirectional replication rule for: %s", source_bucket)

    s3_client.put_bucket_replication(
        # replication rule applied to source bucket
        Bucket=source_bucket,
        ReplicationConfiguration={
            "Role": f"arn:aws:iam::{account_id}:role/service-role/{role_name}",
            # create replication rule
            "Rules": [cross_region_replication_rule],
        },
    )


def create_policy_for_cross_region_replication(
    client: IAMClient,
    *,
    dest_bucket: str,
    dest_kms_key: str,
    dest_region: str,
    source_bucket: str,
    source_kms_key: str,
    source_region: str,
) -> str:
    """Create policy for CCR."""
    policy_name = f"s3crr_kms_for_{source_bucket}_to_{dest_bucket}"
    policy_doc = PolicyDocument(
        Version="2012-10-17",
        Statement=[
            Statement(
                Action=[
                    awacs.s3.GetObjectVersionAcl,
                    awacs.s3.GetObjectVersionForReplication,
                    awacs.s3.GetReplicationConfiguration,
                    awacs.s3.ListBucket,
                ],
                Effect=Allow,
                Resource=[
                    f"arn:aws:s3:::{source_bucket}",
                    f"arn:aws:s3:::{source_bucket}/*",
                ],
                Sid="AllowReplicationOfSourceBucket",
            ),
            Statement(
                Action=[
                    awacs.s3.GetObjectVersionTagging,
                    awacs.s3.ReplicateDelete,
                    awacs.s3.ReplicateObject,
                    awacs.s3.ReplicateTags,
                ],
                Condition=Condition(
                    StringLikeIfExists(
                        {
                            "s3:x-amz-server-side-encryption": ["aws:kms", "AES256"],
                            "s3:x-amz-server-side-encryption-aws-kms-key-id": [
                                dest_kms_key
                            ],
                        }
                    )
                ),
                Effect=Allow,
                Resource=[f"arn:aws:s3:::{dest_bucket}/*"],
                Sid="AllowDestinationBucketToReceiveReplicatedObjects",
            ),
            Statement(
                Action=[awacs.kms.Decrypt],
                Condition=Condition(
                    StringLike(
                        {
                            "kms:ViaService": f"s3.{source_region}.amazonaws.com",
                            "kms:EncryptionContext:aws:s3:arn": [
                                f"arn:aws:s3:::{source_bucket}",  # For bucket key encryption
                                f"arn:aws:s3:::{source_bucket}/*",
                            ],
                        }
                    )
                ),
                Effect=Allow,
                Resource=[source_kms_key],
                Sid="AllowDecryptOfObjectsInSourceBucket",
            ),
            Statement(
                Action=[awacs.kms.Encrypt],
                Condition=Condition(
                    StringLike(
                        {
                            "kms:ViaService": f"s3.{dest_region}.amazonaws.com",
                            "kms:EncryptionContext:aws:s3:arn": [
                                f"arn:aws:s3:::{dest_bucket}",  # For bucket key encryption
                                f"arn:aws:s3:::{dest_bucket}/*",
                            ],
                        }
                    )
                ),
                Effect=Allow,
                Resource=[dest_kms_key],
                Sid="AllowEncryptionOfObjectsInDestinationBucket",
            ),
        ],
    )

    try:
        LOGGER.info("creating IAM policy %s...", policy_name)
        client.create_policy(
            PolicyDocument=policy_doc.to_json(), PolicyName=policy_name
        )
    except client.exceptions.EntityAlreadyExistsException:
        LOGGER.info("skipped creating policy; %s already exists", policy_name)
    return policy_name


def create_role_for_cross_region_replication(
    client: IAMClient,
    *,
    account_id: str,
    bucket_name: str,
    tags: list[TagTypeDef],
) -> str:
    """Create IAM role for source bucket.

    Args:
        client: boto3 IAM client.
        session: boto3 session.
        account_id: AWS account ID.
        bucket_name: S3 bucket name.
        tags: Tags to apply to resources.

    Returns:
        Role name.

    """
    role_name = f"s3crr_role_for_{bucket_name}"

    try:
        LOGGER.info("creating IAM role %s...", role_name)
        client.create_role(
            AssumeRolePolicyDocument=make_simple_assume_policy(
                "s3.amazonaws.com"
            ).to_json(),
            Path="/service-role/",
            PermissionsBoundary=f"arn:aws:iam::{account_id}:policy/swa/SWACSPermissionsBoundary",
            RoleName=role_name,
            Tags=tags,
        )
    except client.exceptions.EntityAlreadyExistsException:
        LOGGER.info("skipped creating role; %s already exists", role_name)
    return role_name


def get_bucket_kms_key_id(
    *,
    account_id: str,
    region: str,
    bucket_name: str,
    session: boto3.Session,
) -> str:
    """Get's the KMS Arn of the bucket or the default SWA KMS Arn.

    If the bucket does not leverage a KMS Arn by default for encryption the default
    SWA KMS Arn will be returned.

    Args:
        account_id: AWS account ID.
        bucket_name: S3 bucket name.
        region: The AWS region.
        session: boto3 session.

    Returns:
        The KMS ARN.
    """
    resp = session.client("s3").get_bucket_encryption(Bucket=bucket_name)
    for rule in resp["ServerSideEncryptionConfiguration"]["Rules"]:
        if (
            "ApplyServerSideEncryptionByDefault" in rule
            and "KMSMasterKeyID" in rule["ApplyServerSideEncryptionByDefault"]
            and rule["ApplyServerSideEncryptionByDefault"].get("KMSMasterKeyID")
        ):
            key = rule["ApplyServerSideEncryptionByDefault"]["KMSMasterKeyID"]
            if "alias" in key:
                resp = session.client("kms").describe_key(KeyId=key)
                if "Arn" in resp["KeyMetadata"]:
                    return resp["KeyMetadata"]["Arn"]
            return key
    return get_kms_key_id(account_id=account_id, region=region, session=session)


def remove_replication(
    source_bucket: str,
    context: CfnginContext,
    department: str,
    module_config_path: StrPath,
) -> None:
    """Remove replication configuration from the source bucket.

    Args:
        session: boto3 session.
        source_bucket: Source bucket name.
        context: Context to grab AWS session from.
        department: Department that is deploying module.
        module_config_path: Path to module config.
    """
    s3_client = context.get_session().client("s3")
    s3_client.delete_bucket_replication(Bucket=source_bucket)

    # Delete replication IAM rules / policies
    delete_cross_region_replication_role(
        context=context, department=department, module_config_path=module_config_path
    )
