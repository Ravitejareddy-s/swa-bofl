#! /usr/bin/env python
"""Call private API gateway to verify account."""
from __future__ import annotations

import argparse
import json
import logging
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
    query_params: dict[str, Any],
    api_url_ssm_param_name: str,
    account_status_path: str,
    api_host_ssm_param_name: str,
    region: str,
) -> dict[str, Any]:
    """Call integration test API and get response."""
    credentials = get_credentials()
    ssm = get_ssm_client(region)

    api_response = requests.get(
        ssm.get_parameter(Name=api_url_ssm_param_name)["Parameter"].get("Value", "")
        + account_status_path,
        auth=AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "execute-api",
            session_token=credentials.token,
        ),
        params=query_params,
        headers={
            "Host": ssm.get_parameter(Name=api_host_ssm_param_name)["Parameter"].get(
                "Value", ""
            )
        },
        timeout=900,
    )
    logging.info("Response received %s", api_response)

    if api_response.status_code == 200:
        response = json.loads(api_response.text)
    else:
        logging.info("Unable to verify account for running integration tests.")
        response = {"jobId": ""}

    return response


def parse_arguments() -> argparse.Namespace:  # cov: ignore
    """Parse arguments."""
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
        "--account-status-path",
        "-c",
        type=str,
        default=None,
        required=True,
        help="The api path for accountStatus.",
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
    parser.add_argument(
        "--account-number",
        "-t",
        type=str,
        default=None,
        required=True,
        help="The Account Number where integration test will run.",
    )
    return parser.parse_args()


def main() -> None:
    """Entrypoint function."""
    args = parse_arguments()

    logging.debug("project_pipeline_id: %s", args.project_pipeline_id)
    logging.debug("api_url_ssm: %s", args.api_url_ssm)
    logging.debug("account_status_path: %s", args.account_status_path)
    logging.debug("api_host_ssm: %s", args.api_host_ssm)
    logging.debug("aws_region: %s", args.aws_region)
    logging.debug("account_number: %s", args.account_number)

    params = {"accountId": args.account_number}
    logging.info("Query params: %s", params)
    response = call_integration_test_api(
        params,
        args.api_url_ssm,
        args.account_status_path,
        args.api_host_ssm,
        args.aws_region,
    )
    logging.info("Response: %s", response)

    job_id_response = response.get("jobId", "")

    if job_id_response != "":
        if job_id_response != args.project_pipeline_id:
            raise Exception(  # noqa: TRY002
                "This account is now running another integration test. "
                "Please re-run the setup job prior to running the integration tests."
            )
        logging.info("Verification Successful. Account is still tied to this jobId.")
    else:
        logging.info("No JobId received in the response. Continuing anyway..")


if __name__ == "__main__":
    main()
