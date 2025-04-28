"""Return S3 prefix list ID.

.. rubric:: Example
.. code-block:: yaml

    lookups:
      s3_prefix_list_id: ccplatcfnginlibs.lookups.S3PrefixListIdLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${s3_prefix_list_id }

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from runway.lookups.handlers.base import LookupHandler

if TYPE_CHECKING:
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


class S3PrefixListIdLookup(LookupHandler["CfnginContext"]):
    """CFNgin lookup."""

    TYPE_NAME: ClassVar[str] = "s3_prefix_list_id"

    @classmethod
    def handle(
        cls,
        value: str,  # noqa: ARG003
        context: CfnginContext,
        *__args: Any,
        **__kwargs: Any,
    ) -> str | None:
        """Handle the lookup for S3 endpoint."""
        prefix_lists = (
            context.get_session().client("ec2").describe_prefix_lists()["PrefixLists"]
        )

        for prefix_list in prefix_lists:
            if "PrefixListName" in prefix_list and prefix_list[
                "PrefixListName"
            ].endswith("s3"):
                LOGGER.info("prefix list found: %s", prefix_list.get("PrefixListId"))
                return prefix_list.get("PrefixListId")
        return None
