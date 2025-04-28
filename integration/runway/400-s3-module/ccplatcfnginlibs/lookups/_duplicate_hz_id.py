"""Get Hosted Zone ID of Public or Private Hosted Zone."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

import yaml
from runway.lookups.handlers.base import LookupHandler

from ._ssm_param import SSMParamLookup

if TYPE_CHECKING:
    from mypy_boto3_route53.type_defs import (
        HostedZoneConfigTypeDef,
        HostedZoneTypeDef,
    )
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


class DuplicateHZIdLookup(LookupHandler["CfnginContext"]):
    """Lookup Hosted Zone ID."""

    TYPE_NAME: ClassVar[str] = "hz_id"

    @classmethod
    def handle(
        cls, value: str, context: CfnginContext, *__args: Any, **__kwargs: Any
    ) -> Any:
        """Return the ID of a Hosted Zone."""
        if "," in value:
            # Handles comma-separated values from stacker.yml
            config_params = value.split(",")
            if len(config_params) < 4:
                raise ValueError(
                    "Comma-separated format must include all four values: "
                    "duplicate_hz,use_public_hosted_zone,hosted_zone_name,hosted_zone_ssm_path"
                )
            hosted_zone_config = {
                "duplicate_hz": str(config_params[0]).lower() == "true",
                "use_public_hosted_zone": str(config_params[1]).lower() == "true",
                "hosted_zone_name": (
                    config_params[2] if config_params[2] != "null" else None
                ),
                "hosted_zone_ssm_path": (
                    config_params[3] if config_params[3] != "null" else None
                ),
            }
            LOGGER.debug(hosted_zone_config)

        else:
            # Handle YAML string input
            hosted_zone_config: dict[str, Any] = yaml.safe_load(value)
            LOGGER.debug(hosted_zone_config)

        hz_name: str = ""
        use_private_hz: bool = not hosted_zone_config.get(
            "use_public_hosted_zone", False
        )
        LOGGER.debug(hosted_zone_config)

        if hosted_zone_config["hosted_zone_name"] is not None:
            hz_name = hosted_zone_config["hosted_zone_name"]
        elif hosted_zone_config["hosted_zone_ssm_path"] is not None:
            hz_name = SSMParamLookup.handle(
                hosted_zone_config["hosted_zone_ssm_path"], context
            )
        else:
            return hz_name

        if not hz_name.endswith("."):
            hz_name = hz_name + "."

        client = context.get_session().client("route53")
        hosted_zones: list[HostedZoneTypeDef] = client.list_hosted_zones_by_name(
            DNSName=hz_name
        )["HostedZones"]
        for hosted_zone in hosted_zones:
            hz_config: HostedZoneConfigTypeDef | None = hosted_zone.get("Config")
            if (
                hosted_zone.get("Name").lower() == hz_name.lower()
                and hz_config
                and (hz_config.get("PrivateZone") == use_private_hz)
            ):
                LOGGER.debug(hosted_zone["Id"])
                return hosted_zone["Id"].split("/")[2]
        raise ValueError(f"Hosted Zone not found for name: {hz_name}")
