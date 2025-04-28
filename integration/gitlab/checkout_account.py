#! /usr/bin/env python
"""Call private API gateway to auth user to deploy to AWS."""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import boto3
import requests
from requests_aws4auth import AWS4Auth

if TYPE_CHECKING:
    from botocore.credentials import Credentials
    from mypy_boto3_ssm.client import SSMClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s]-[%(lineno)d]  %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)
MAX_RETRY_TIME_SECONDS = 15 * 60  # seconds
SLEEP_TIME = 15


def get_credentials() -> Credentials:  # cov: ignore
    """Return AWS credentials."""
    result = boto3.Session().get_credentials()
    if result is not None:
        return result
    raise ValueError("AWS credentials could not be retrieved")


def get_ssm_client(region: str) -> SSMClient:  # cov: ignore
    """Return SSM client."""
    return boto3.client("ssm", region_name=region)


def call_integration_test_api(
    request_body: object,
    api_url_ssm_param_name: str,
    checkout_path: str,
    api_host_ssm_param_name: str,
    region: str,
) -> dict[str, Any]:
    """Call API gateway authorize-aws-deployment and return the response."""
    credentials = get_credentials()
    ssm = get_ssm_client(region)

    api_response = get_response(
        ssm.get_parameter(Name=api_url_ssm_param_name)["Parameter"].get("Value", "")
        + checkout_path,
        AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "execute-api",
            session_token=credentials.token,
        ),
        request_body,
        {
            "Host": ssm.get_parameter(Name=api_host_ssm_param_name)["Parameter"].get(
                "Value", ""
            )
        },
    )
    if api_response.status_code == 200:
        response = json.loads(api_response.text)
    else:
        response = {
            "message": "Account Checkout Failed. Please create a ticket for EC "
            "OPS team so that they can look at this issue.",
            "accountId": None,
        }
    return response


def get_response(
    url: str, awsauth: AWS4Auth, payload: object, headers: dict[str, str]
) -> requests.Response:
    """Retry until a response is received or for a total of MAX_RETRY_TIME_SECONDS."""
    api_response = requests.post(
        url, auth=awsauth, json=payload, headers=headers, timeout=900
    )
    logging.info("Response received %s", api_response)
    total_wait = 0
    while api_response.status_code != 200 and total_wait < MAX_RETRY_TIME_SECONDS:
        logging.info("Retrying after 15 seconds for a total of 15 minutes")
        time.sleep(SLEEP_TIME)
        total_wait += SLEEP_TIME
        api_response = requests.post(
            url, auth=awsauth, json=payload, headers=headers, timeout=900
        )
    return api_response


def write_account_number_txt(aws_account_number: str) -> None:
    """Write to a file that will contain the account number for integration tests."""
    Path("account_number.txt").write_text(aws_account_number)


def parse_arguments() -> argparse.Namespace:  # cov: ignore
    """Parse arguments for the script."""
    parser = argparse.ArgumentParser(
        description="Interface for calling ec2 environment access service."
    )
    parser.add_argument(
        "--project-pipeline-id",
        "-j",
        type=str,
        default=None,
        required=True,
        help="A concatinated project id and pipeline id from which the user is requesting access.",
    )
    parser.add_argument(
        "--api-url-ssm",
        "-u",
        type=str,
        default=None,
        required=True,
        help="The ssm param name for url for integration test api.",
    )
    parser.add_argument(
        "--checkout-path",
        "-c",
        type=str,
        default=None,
        required=True,
        help="The api path for checkout.",
    )
    parser.add_argument(
        "--api-host-ssm",
        "-a",
        type=str,
        default=None,
        required=True,
        help="The ssm param name for Host header for api gw for integration test api.",
    )
    parser.add_argument(
        "--aws-region",
        "-r",
        type=str,
        default=None,
        required=True,
        help="The aws region in which the ec2 environment access service resides.",
    )
    return parser.parse_args()


def main() -> None:
    """Entrypoint function."""
    args = parse_arguments()

    logging.debug("project_pipeline_id: %s", args.project_pipeline_id)
    logging.debug("api_url_ssm: %s", args.api_url_ssm)
    logging.debug("checkout_path: %s", args.checkout_path)
    logging.debug("api_host_ssm: %s", args.api_host_ssm)
    logging.debug("aws_region: %s", args.aws_region)

    body = {"jobId": args.project_pipeline_id}
    logging.info("body: %s", body)
    response = call_integration_test_api(
        body,
        args.api_url_ssm,
        args.checkout_path,
        args.api_host_ssm,
        args.aws_region,
    )
    logging.info("Response: %s", response)
    if response["accountId"] is not None:
        write_account_number_txt(response["accountId"])
    else:
        logging.info("Unable to checkout account")
        raise Exception("Unable to checkout account")  # noqa: TRY002


if __name__ == "__main__":
    main()
