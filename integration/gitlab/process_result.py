"""Process results."""

from __future__ import annotations

import argparse
import logging

import boto3
import requests
from requests_aws4auth import AWS4Auth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s]-[%(lineno)d]  %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)


def parse_arguments() -> argparse.Namespace:  # cov: ignore
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        description="Interface for calling integration test account service."
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
        help="The aws region in which the integration test account service resides.",
    )
    parser.add_argument(
        "--condition",
        "-c",
        type=str,
        default=None,
        required=True,
        help="The condition of the job, success or completed.",
    )
    return parser.parse_args()


def call_integration_test_api(
    request_body: object,
    api_url_ssm_param_name: str,
    checkout_path: str,
    api_host_ssm_param_name: str,
    region: str,
) -> requests.Response:  # cov: ignore
    """Call API gateway authorize-aws-deployment and return the response."""
    session = boto3.Session()
    credentials = session.get_credentials()
    if credentials is None:
        raise ValueError("AWS credentials could not be retrieved")
    ssm = session.client("ssm", region_name=region)

    return requests.post(
        (
            ssm.get_parameter(Name=api_url_ssm_param_name)["Parameter"].get("Value", "")
            + checkout_path
        ),
        auth=AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "execute-api",
            session_token=credentials.token,
        ),
        json=request_body,
        headers={
            "Host": ssm.get_parameter(Name=api_host_ssm_param_name)["Parameter"].get(
                "Value", ""
            )
        },
        timeout=900,
    )


def main() -> None:  # cov: ignore
    """Entrypoint function."""
    args = parse_arguments()
    logging.info("Marking Job as %s", args.condition)
    body = {"jobId": args.project_pipeline_id, "jobStatus": args.condition}
    logging.info("body: %s", body)
    logging.info(
        "Response: %s",
        call_integration_test_api(
            body,
            args.api_url_ssm,
            "/integrationtestsvc/jobStatus",
            args.api_host_ssm,
            args.aws_region,
        ),
    )


if __name__ == "__main__":  # cov: ignore
    main()
