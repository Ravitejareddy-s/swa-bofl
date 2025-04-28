"""Helper used to deploy artifacts using the landing zone distributed deployment engine.

This helper expects the following ssm parameters to exist in the account
that the helper is executed.

landing_zone_bucket_name - The name of the S3 bucket use to upload the artifact for deployment
landing_zone_api_id - The api_id of the api gateway used to make landing zone api calls
landing_zone_kms_key - The kms key used to encrypt the artifact uploaded to the bucket

"""

from __future__ import annotations

import base64
import concurrent.futures
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import boto3
import requests
from deprecated import deprecated

from . import ssm

if TYPE_CHECKING:
    from _typeshed import StrPath
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.type_defs import PutObjectOutputTypeDef

API_CALL_SLEEP = 10
DEFAULT_TIMEOUT = 900

LOGGER = logging.getLogger(__name__)


# TODO(kyle): remove this - it is more harmful than helpful
@deprecated(reason="boto3 sessions should be created from CFNgin's context object")
def get_s3_client(region: str | None) -> S3Client:  # cov: ignore
    """Return the S3 client."""
    return boto3.client("s3", region_name=region)


@deprecated(reason="use 'ssm' lookup or get_parameter directly")
def get_lz_bucket() -> str:  # cov: ignore
    """Retrieve the landing zone bucket name from parameter store."""
    return ssm.get_parameter("landing_zone_bucket_name") or ""


@deprecated(reason="use 'ssm' lookup or get_parameter directly")
def get_lz_api_id() -> str:  # cov: ignore
    """Retrieve the landing zone api id from parameter store."""
    return ssm.get_parameter("landing_zone_api_id") or ""


@deprecated(reason="use 'ssm' lookup or get_parameter directly")
def get_lz_kms_key() -> str:  # cov: ignore
    """Retrieve the landing zone kms key id from parameter store."""
    return ssm.get_parameter("landing_zone_kms_key") or ""


def check_deployment(etag: str, region: str, env: str, timeout: int) -> bool:
    """Check if the deployment was successful.

    Args:
        etag: The etag of the artifact that was deployed.
        region: The region the artifact was deployed to.
        env: The environment the artifact was deployed to.
        timeout: The number of seconds to wait for the deployment to complete.

    Returns:
        Whether the deployment was successful.

    """
    endpoint_url = (
        f"https://{get_lz_api_id()}.execute-api.{region}.amazonaws.com/"
        f"{env}/deployment/{etag}"
    )
    credential = base64.b64encode(str(uuid.uuid1()).encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {credential}",
    }
    status = None
    end_time = datetime.now() + timedelta(seconds=timeout)
    while status is None and datetime.now() < end_time:
        time.sleep(API_CALL_SLEEP)
        LOGGER.debug("calling api")
        api_resp = requests.get(endpoint_url, headers=headers, timeout=900)
        api_resp.raise_for_status()
        resp_json = json.loads(api_resp.text)
        if "Items" in resp_json:
            status = deployment_status(resp_json["Items"])
    return bool(status)


def deploy_artifact(
    artifact_path: str,
    s3_prefix: str,
    region: str,
    env: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> bool:
    """Deploy a deployment artifact.

    Args:
        artifact_path: The path to the artifact to deploy.
        s3_prefix: The prefix to use when uploading the artifact to S3.
        region: The region to deploy the artifact to.
        env: The environment to deploy the artifact to.
        timeout: The number of seconds to wait for the deployment to complete.

    Returns:
        Whether or not deployment of artifacts was successful.

    """
    try:
        etag = upload_artifact(artifact_path, s3_prefix, region)
        if etag:
            return check_deployment(etag, region, env, timeout)
    except Exception:
        LOGGER.exception(
            "exception occurred while deploying artifact %s", artifact_path
        )
    return False


def deploy_artifacts(
    artifact_paths: list[str],
    s3_prefix: str,
    region: str,
    env: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> bool:
    """Deploy multiple deployment artifacts simultaneously.

    Returns:
        Whether or not deployment of artifacts was successful.

    """
    response = True
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(
                deploy_artifact, artifact_path, s3_prefix, region, env, timeout
            ): artifact_path
            for artifact_path in artifact_paths
        }

        for future in concurrent.futures.as_completed(futures, timeout=timeout + 60):
            response = response and future.result()
    return response


def deployment_status(items: list[dict[str, Any]]) -> bool | None:
    """Iterate though all deployment items and determines status.

    Args:
        items: The list of deployment items.

    Returns:
        True - if deployment in CREATE_COMPLETE or UPDATE_COMPLETE status
        False - if deployment in and FAILED or ROLLBACK status
        None - if deployment not in any COMPLETE, FAILED or ROLLBACK state

    """
    response = None
    success_matches = ["CREATE_COMPLETE", "UPDATE_COMPLETE"]
    failed_matches = ["FAILED", "ROLLBACK"]
    for item in items:
        if any(x in item["Message"]["S"] for x in success_matches):
            response = True
        elif any(x in item["Message"]["S"] for x in failed_matches):
            return False
    return response


@deprecated(reason="use put_object directly")
def put_object(
    bucket: str, key: str, object_path: StrPath, region: str | None = None
) -> PutObjectOutputTypeDef:
    """Put the object defined by the object path in the S3 bucket using the given key.

    Args:
        bucket: The name of the bucket to put the object in.
        key: The key to use when putting the object in the bucket.
        object_path: The path to the object to put in the bucket.
        region: The region to put the object in.

    """
    return get_s3_client(region).put_object(
        ACL="bucket-owner-full-control",
        Body=Path(object_path).read_bytes(),
        Bucket=bucket,
        Key=key,
        SSEKMSKeyId=get_lz_kms_key(),
        ServerSideEncryption="aws:kms",
    )


def upload_artifact(artifact_path: str, s3_prefix: str, region: str) -> str | None:
    """Upload the artifact for deployment.

    Args:
        artifact_path: The path to the artifact to deploy.
        s3_prefix: The prefix to use when uploading the artifact to S3.
        region: The region to deploy the artifact to.

    Returns:
        Etag id from s3 response.

    """
    return (
        put_object(
            get_lz_bucket(),
            f"{s3_prefix}/{artifact_path.split('/')[-1]}",
            artifact_path,
            region,
        )
        .get("ETag", "")
        .replace('"', "")
        or None
    )
