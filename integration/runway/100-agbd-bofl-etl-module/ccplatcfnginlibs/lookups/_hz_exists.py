"""Check if a Hosted Zone exists.

:Query Syntax: ``<domain-name>``

This is often used in tandem with ``hz_name`` to get the ID of a the Hosted Zone it returns.

.. rubric:: Example
.. code-block:: yaml

    lookups:
      hz_exists: ccplatcfnginlibs.lookups.HzExistsLookup
      hz_name: ccplatcfnginlibs.lookups.HzNameLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${hz_region ${hz_name }}

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from runway.lookups.handlers.base import LookupHandler

from ._hz_id import HzIdLookup
from ._hz_region import HzRegionLookup

if TYPE_CHECKING:
    from runway.context import CfnginContext


class HzExistsLookup(LookupHandler["CfnginContext"]):
    """Check if a Hosted Zone exists."""

    TYPE_NAME: ClassVar[str] = "hz_exists"

    @classmethod
    def handle(
        cls, value: str, context: CfnginContext, *args: Any, **kwargs: Any
    ) -> bool:
        """Return True/False if a Hosted Zone exists within the environment."""
        hz_name, _args = cls.parse(value)
        try:
            hz_id = HzIdLookup.handle(
                hz_name, context=context, *args, **kwargs  # noqa: B026
            )
        except ValueError as exc:
            if "Hosted Zone not found for name: " in str(exc):
                return False
            raise
        # if Hosted Zone found in same region, CFN should maintain it
        return context.env.aws_region != HzRegionLookup.handle(
            hz_id, context=context, *args, **kwargs  # noqa: B026
        )
