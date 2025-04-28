"""Get private Hosted Zone ID.

:Query Syntax: ``<domain-name>``

This is often used in tandem with ``hz_name`` to get the ID of a the Hosted Zone it returns.

.. rubric:: Example
.. code-block:: yaml

    lookups:
      hz_name: ccplatcfnginlibs.lookups.HzNameLookup
      hz_id: ccplatcfnginlibs.lookups.HzIdLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${hz_id ${hz_name }}

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from runway.lookups.handlers.base import LookupHandler

if TYPE_CHECKING:
    from mypy_boto3_route53.type_defs import HostedZoneConfigTypeDef, HostedZoneTypeDef
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


class HzIdLookup(LookupHandler["CfnginContext"]):
    """Lookup Hosted Zone ID."""

    TYPE_NAME: ClassVar[str] = "hz_id"

    @classmethod
    def handle(cls, value: str, context: CfnginContext, **__kwargs: Any) -> Any:
        """Return the ID of the private Hosted Zone attached to the VPC."""
        hz_name, args = cls.parse(value)
        client = context.get_session().client("route53")

        hosted_zones: list[HostedZoneTypeDef] = client.list_hosted_zones_by_name(
            DNSName=hz_name
        )["HostedZones"]
        for hosted_zone in hosted_zones:
            hz_config: HostedZoneConfigTypeDef | None = hosted_zone.get("Config")
            if (
                hosted_zone.get("Name").lower() == hz_name.lower()
                and hz_config
                and hz_config.get("PrivateZone")
            ):
                return cls.format_results(hosted_zone["Id"].split("/")[2], **args)

        if "default" in args:
            LOGGER.debug(
                'unable to resolve lookup for Hosted Zone "%s"; using default',
                hz_name,
                exc_info=True,
            )
            args.pop("load", None)  # don't load a default value
            return cls.format_results(args.pop("default"), **args)

        raise ValueError(f"Hosted Zone not found for name: {hz_name}")
