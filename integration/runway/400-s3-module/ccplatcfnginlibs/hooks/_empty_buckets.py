"""Empty S3 Buckets from config file.

:Path: ``ccplatcfnginlibs.hooks.empty_buckets``

.. rubric:: Example
.. code-block:: yaml

  pre_destroy:
    - path: ccplatcfnginlibs.hooks.empty_buckets
      args:
        department: ${department}
        module_config_path: ${module_config}

"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml
from botocore.exceptions import ClientError
from pydantic import Field
from runway.utils import BaseModel

if TYPE_CHECKING:
    from _typeshed import StrPath
    from runway.context import CfnginContext


class BucketConfigDataModel(BaseModel):
    """Bucket configuration data model."""

    name: str
    """Name of the bucket."""

    cross_region: Optional[str] = Field(default=None, alias="crossRegion")
    """The AWS region to replicate to."""

    cross_region_destination_bucket: Optional[str] = Field(
        default=None, alias="crrDestinationBucket"
    )
    """The name of the destination bucket in the cross region."""


class ModuleConfigDataModel(BaseModel):
    """Module configuration data model."""

    bucket_list: list[BucketConfigDataModel] = Field(default=[], alias="vBucketList")
    """List of buckets to configure."""


def empty_buckets(
    context: CfnginContext,
    *__args: Any,
    department: str,
    module_config_path: StrPath,
    **__kwargs: Any,
) -> bool:
    """Empty S3 Buckets from config file.

    Bucket logging is disabled before it is emptied.

    Args:
        context: CFNgin context object.
        department: Name of the department.
        module_config_path: Path to module config file.

    """
    bucket_list = ModuleConfigDataModel.model_validate(
        yaml.safe_load(Path(module_config_path).read_bytes())
    ).bucket_list
    bucket_names = {
        f"{department}-{context.env.aws_region}-{context.namespace}-{bucket.name}"
        for bucket in bucket_list
    }
    bucket_names.update(
        {
            (
                bucket.cross_region_destination_bucket
                or f"{department}-{bucket.cross_region}-{context.namespace}-{bucket.name}"
            )
            for bucket in bucket_list
            if bucket.cross_region
        }
    )

    resource = context.get_session().resource("s3")
    # needs to be sorted to ensure calls are made in a consistent order for tests
    for bucket_name in sorted(bucket_names):
        try:  # check to see if bucket exists
            resource.meta.client.head_bucket(Bucket=bucket_name)
        except ClientError:
            continue
        bucket = resource.Bucket(bucket_name)
        bucket.Logging().put(BucketLoggingStatus={})
        bucket.object_versions.delete()
    return True
