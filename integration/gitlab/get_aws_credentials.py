#! /usr/bin/env python
"""Call private API gateway to auth user to deploy to AWS."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import boto3
import requests
from requests_aws4auth import AWS4Auth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-9s] [%(filename)s]-[%(lineno)d]  %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)


def call_aws_authorization_deployment_api(
    request_body: object, api_url_ssm_param_name: str, region: str, api_host: str
) -> requests.Response:  # cov: ignore
    """Call API gateway authorize-aws-deployment and return the response."""
    session = boto3.Session()
    credentials = session.get_credentials()
    if credentials is None:
        raise ValueError("AWS credentials could not be retrieved")

    return requests.post(
        session.client("ssm", region_name=region)
        .get_parameter(Name=api_url_ssm_param_name)["Parameter"]
        .get("Value", ""),
        auth=AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "execute-api",
            session_token=credentials.token,
        ),
        json={"body": request_body},
        headers={"Host": api_host},
        timeout=900,
    )


def log_authorization_response(
    accounts: list[str], response: requests.Response
) -> None:  # cov: ignore
    """Log Unauthorized 401 response for user & fail, log success message, or any nonsuccessful."""
    if response.status_code == 401:
        aws_accounts_str = " ".join(accounts)
        raise Exception(  # noqa: TRY002
            f"401 Unauthorized - Not authorized to deploy to aws account: "
            f"{aws_accounts_str}!"
        )
    if response.status_code == 200:
        write_aws_setup_script(json.loads(response.text)["body"])
        logging.info(
            "result: %s",
            "200 Success - AWS AccessKeyId, AWS Expiration, AWS "
            "SecretAccessKey, and AWS SessionToken have been successfully "
            "added to $SET_UP_AWS script file",
        )
    else:
        logging.error(response)
        logging.error("Error Received. Response Text: %s", response.text)
        logging.error("Error Received. Status Code: %s", response.status_code)
        raise Exception(  # noqa: TRY002
            f"{response.status_code} Unsuccessful AWS Authentication attempt - "
            f"the following error occurred: {response.text}"
        )


def write_aws_setup_script(aws_creds: dict[str, str]) -> None:  # cov: ignore
    """Write a script to set AWS cred env vars based on GtiLab CI/CD variables."""
    script = Path(".set_up_aws.sh")
    with script.open("w") as file_object:
        file_object.write(
            f'export AWS_SECRET_ACCESS_KEY={aws_creds["SecretAccessKey"]}\n'
        )
        file_object.write(f'export AWS_SESSION_TOKEN={aws_creds["SessionToken"]}\n')
        file_object.write(f'export AWS_ACCESS_KEY_ID={aws_creds["AccessKeyId"]}\n')
        file_object.write("export AWS_DEFAULT_REGION=us-east-1\n")
        file_object.write(
            'echo "echo \\"ERROR: Please run the setup job before running the deployment job!\\"'
        )
        file_object.write(f';exit 1" > {script.name}\n')
    script.chmod(0o755)


def parse_arguments(arguments: list[str]) -> argparse.Namespace:  # cov: ignore
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        description="Interface for calling ec2 environment access service."
    )
    parser.add_argument(
        "--project-id",
        "-p",
        type=str,
        default=None,
        required=True,
        help="Project id from which the user is requesting access.",
    )
    parser.add_argument(
        "--environment",
        "-e",
        type=str,
        default=None,
        required=True,
        help="Environment that the user is requesting access to.",
    )
    parser.add_argument(
        "--api-url-ssm-param-name",
        "-s",
        type=str,
        default=None,
        required=True,
        help="The ssm param name that can be used to fetch the api url.",
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
        "--api-host",
        "-a",
        type=str,
        default=None,
        required=True,
        help="The aws api gateway host for the ec2 environment access service.",
    )
    parser.add_argument(
        "--integration-test-account",
        "-it",
        type=str,
        default=None,
        required=False,
        help="The CCP Integration test account that will be utilized for running integration tests",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str]) -> None:  # cov: ignore
    """Entrypoint function."""
    args = parse_arguments(arguments)

    logging.debug("project_id: %s", args.project_id)
    logging.debug("environment: %s", args.environment)
    logging.debug("api_url_ssm_param_name: %s", args.api_url_ssm_param_name)
    logging.debug("aws_region: %s", args.aws_region)
    logging.debug("api_host: %s", args.api_host)
    logging.debug("integration_test_account: %s", args.integration_test_account)

    aws_accounts = [args.integration_test_account]

    body = {
        "environment": args.environment,
        "project_id": args.project_id,
        "aws_account_numbers": aws_accounts,
    }
    logging.info("body: %s", body)
    api_response = call_aws_authorization_deployment_api(
        body, args.api_url_ssm_param_name, args.aws_region, args.api_host
    )
    log_authorization_response(aws_accounts, api_response)


if __name__ == "__main__":  # cov: ignore
    main(sys.argv[1:])
