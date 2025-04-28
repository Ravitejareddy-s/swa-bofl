"""Get Value from SSM Parameter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from runway.lookups.handlers.base import LookupHandler

if TYPE_CHECKING:
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


class SSMParamLookup(LookupHandler["CfnginContext"]):
    """CFNgin Lookup."""

    TYPE_NAME: ClassVar[str] = "ssm_param"

    @classmethod
    def handle(cls, value: str, context: CfnginContext, **__kwargs: Any) -> str:
        """Lookup SSM Parameter."""
        if value != "default":
            LOGGER.info("Looking for parameter in %s", value)

            client = context.get_session().client("ssm")
            param = client.get_parameter(
                Name=value,
                WithDecryption=True,
            )["Parameter"]
            if "Value" in param:
                return param["Value"]
        return ""
