"""Constants."""

import os

AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
"""AWS region from environment variables."""

KMS_KEY_IDS = {
    "us-east-1": "arn:aws:kms:us-east-1:602788979237:key/2cdd488f-89b6-416e-9a30-a03708d1d3df",
    "us-east-2": "arn:aws:kms:us-east-2:602788979237:key/e65664c1-1415-4042-a812-a431b9da6bf1",
    "us-west-2": "arn:aws:kms:us-west-2:602788979237:key/6962dfad-19da-4e78-810b-9df72326f793",
    "eu-central-1": "arn:aws:kms:eu-central-1:602788979237:key/84b02a32-bb6c-4e85-80d6-0bf23f0520bb",
    "eu-west-1": "arn:aws:kms:eu-west-1:602788979237:key/501a8eee-6396-4fb7-bcca-5bb5d51bcdd2",
}
"""Mapping of KMS Key IDs per-region."""

KMS_KEY_GRANT_OPERATIONS = (
    "CreateGrant",
    "Decrypt",
    "DescribeKey",
    "Encrypt",
    "GenerateDataKey",
    "GenerateDataKeyWithoutPlaintext",
    "ReEncryptFrom",
    "ReEncryptTo",
)
"""KMS Key grant operations."""

SUPPORTED_AWS_REGIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-2",
    "eu-central-1",
    "eu-west-1",
]
"""Supported AWS regions."""
