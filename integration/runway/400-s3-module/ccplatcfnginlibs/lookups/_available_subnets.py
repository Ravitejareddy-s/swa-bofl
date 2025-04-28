"""Get a list of available subnets for a given subnet type.

The result is returned as a comma delimited list.

:Query Syntax: ``<network-tier>[,...]``

.. deprecated:: 5.5.0

.. rubric:: Example
.. code-block:: yaml

    lookups:
      available_subnets: ccplatcfnginlibs.lookups.AvailableSubnetsLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${available_subnets internal,private}

"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Any, ClassVar

from deprecated import deprecated
from runway.lookups.handlers.base import LookupHandler
from runway.lookups.handlers.cfn import CfnLookup

try:
    from runway.cfngin.exceptions import (
        StackDoesNotExistError,  # noqa: F401, PGH003, RUF100  # pyright: ignore
    )
except ImportError:
    from runway.cfngin.exceptions import (
        StackDoesNotExist as StackDoesNotExistError,  # noqa: F401, PGH003, RUF100  # pyright: ignore
    )

if TYPE_CHECKING:
    from collections.abc import Mapping

    from runway.cfngin.providers.aws.default import Provider
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


@deprecated(
    reason="use the 'cfn' lookup instead; this will be removed in the next major release"
)
class AvailableSubnetsLookup(  # TODO (kyle): remove in v6.0.0
    LookupHandler["CfnginContext"]
):
    """Get all available subnets."""

    TYPE_NAME: ClassVar[str] = "available_subnets"

    @classmethod
    def get_vpc_outputs(
        cls,
        context: CfnginContext,
        provider: Provider,
    ) -> dict[str, str]:
        """Get VPC Stack Outputs.

        Handles Stack not existing, retaining previous warning statement.

        """
        stack_name = f"{context.parameters.get('networking_tier_namespace', context.namespace)}-vpc"
        try:
            return provider.get_outputs(stack_name)
        except StackDoesNotExistError:
            LOGGER.warning(
                "%s Stack not found; unable to get available Subnets", stack_name
            )
        return {}

    @classmethod
    def handle(
        cls,
        value: str,
        context: CfnginContext,
        *__args: Any,
        provider: Provider,
        **__kwargs: Any,
    ) -> str:
        """Get all available subnets.

        Raises:
            ValueError: Unable to determine module version.

        """
        query, args = cls.parse(value)
        vpc_outputs = cls.get_vpc_outputs(context, provider)
        subnet_tiers = [i.strip() for i in query.split(",")]
        if not vpc_outputs:
            return cls.handle_return(args)
        if "ModuleVersion" not in vpc_outputs:
            raise ValueError(
                "VPC Stack is missing ModuleVersion Output, can't determine how to proceed. "
                "Ensure you are using a compatible version of the cloud-common-vpc-module."
            )
        try:
            vpc_major_version = int(vpc_outputs["ModuleVersion"].strip("v")[0])
        except ValueError:
            LOGGER.warning(
                "non-integer VPC ModuleVersion %s; interpreting as 0.0.0",
                vpc_outputs["ModuleVersion"],
            )
            vpc_major_version = 0
        if vpc_major_version == 0 or vpc_major_version > 6:
            return cls._handle_vpc(args, context, provider, subnet_tiers)
        return cls._handle_legacy_vpc(args, subnet_tiers, vpc_outputs)

    @classmethod
    def _handle_legacy_vpc(
        cls,
        args: Mapping[str, object],
        subnet_tiers: list[str],
        vpc_outputs: dict[str, str],
    ) -> str:
        """Handle getting Subnet IDs from legacy VPC module versions."""
        return cls.handle_return(
            args,
            subnet_tiers=subnet_tiers,
            value=[
                output_value
                for tier in subnet_tiers
                for output_name, output_value in vpc_outputs.items()
                if output_name.lower().startswith(f"{tier.strip().lower()}subnet")
                and output_value.startswith("subnet")
            ],
        )

    @classmethod
    def _handle_vpc(
        cls,
        args: Mapping[str, object],
        context: CfnginContext,
        provider: Provider,
        subnet_tiers: list[str],
    ) -> str:
        """Handle getting Subnet IDs from VPC module."""
        namespace = context.parameters.get(
            "networking_tier_namespace", context.namespace
        )
        return cls.handle_return(
            args,
            subnet_tiers=subnet_tiers,
            value=[
                CfnLookup.handle(
                    f"{namespace}-{tier}-subnet-{index}.Subnet::default=None",
                    context,
                    provider=provider,
                )
                for tier in subnet_tiers
                for index in (0, 1, 2, 3)
            ],
        )

    @classmethod
    def handle_return(
        cls,
        args: Mapping[str, Any],
        *,
        subnet_tiers: list[str] | None = None,
        value: list[str] | None = None,
    ) -> str:
        """Handle return value.

        Accounts for default value, joining final string, logging result, and raising
        an error if needed.

        Raises:
            ValueError: No Subnets were found for the tiers requested.

        """
        if value:
            value = sorted(i for i in value if i)
            LOGGER.info(
                "Found %s available subnets for types [%s]: %s",
                len(value),
                ", ".join(subnet_tiers or ["undefined"]),
                ", ".join(value),
            )
            return ",".join(value)
        copy_args = dict(deepcopy(args))
        if not value and "default" in args:
            copy_args.pop("load", None)  # don't load a default value
            return cls.format_results(copy_args.pop("default"), **args)
        raise ValueError(
            f"no Subnets found for tier(s) {', '.join(subnet_tiers)}"
            if subnet_tiers
            else "could not determine value and no default provided"
        )
