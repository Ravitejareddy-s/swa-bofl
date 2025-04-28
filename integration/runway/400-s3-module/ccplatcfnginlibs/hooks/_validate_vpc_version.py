"""Validate VPC Exists and validate version.

:Path: ``ccplatcfnginlibs.hooks.validate_vpc_version``

.. rubric:: Example
.. code-block:: yaml

  pre_deploy:
    - path: ccplatcfnginlibs.hooks.validate_vpc_version
      args:
        validate_vpc: true  # default: false

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from runway.lookups.handlers.ssm import SsmLookup
from runway.utils import Version, str_to_bool

if TYPE_CHECKING:
    from runway.cfngin.providers.aws.default import Provider
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)

DEFAULT_VPC_MODULE_MAJOR_VERSION = 4


def validate_vpc_version(
    context: CfnginContext,
    *__args: Any,
    provider: Provider,
    validate_vpc: bool | str = False,
    **__kwargs: Any,
) -> bool:
    """Check that the VPC module is deployed, and that its major version is correct.

    Args:
        context: The context object.
        provider: The provider object.
        validate_vpc: Whether to validate the VPC module.

    Raises:
        ValueError: If the VPC module major version is incorrect.

    """
    if str_to_bool(validate_vpc):
        expected_major_version = int(
            context.parameters.get(
                "vpc_module_major_version", DEFAULT_VPC_MODULE_MAJOR_VERSION
            )
        )
        networking_namespace = (
            context.parameters.get("networking_tier_namespace") or context.namespace
        )
        LOGGER.info("expected major version: %s", expected_major_version)
        LOGGER.info("networking namespace: %s", networking_namespace)

        try:
            vpc_version_str = provider.get_output(
                f"{networking_namespace}-vpc", "ModuleVersion"
            )
            LOGGER.info("VPC module version: %s", vpc_version_str)
        except KeyError:
            LOGGER.exception(
                "VPC stack missing output ModuleVersion (added in v4.0.0); "
                "trying legacy method of checking VPC version..."
            )
            vpc_version_str = SsmLookup.handle(
                f"/ccplat/{networking_namespace}/cloud-common-vpc-module/params/module_version",
                context,
            )
            LOGGER.info("legacy VPC module version found: %s", vpc_version_str)

        if vpc_version_str in ["SNAPSHOT", "local"]:
            LOGGER.info("VPC running in %s mode", vpc_version_str)
            return True

        vpc_version = Version(vpc_version_str)
        if vpc_version.major == expected_major_version:
            LOGGER.info(
                "VPC module version %s matches expected major version %s",
                vpc_version,
                expected_major_version,
            )
            return True
        raise ValueError(
            f"VPC module version {vpc_version} doesn't match expected major version "
            f"{expected_major_version}"
        )
    LOGGER.info("skipped VPC validation")
    return True
