"""Get private Hosted Zone name.

.. rubric:: Example
.. code-block:: yaml

    lookups:
      hz_name: ccplatcfnginlibs.lookups.HzNameLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${hz_name }

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from runway.lookups.handlers.base import LookupHandler

if TYPE_CHECKING:
    from runway.context import CfnginContext


class HzNameLookup(LookupHandler["CfnginContext"]):
    """Lookup Hosted Zone name."""

    TYPE_NAME: ClassVar[str] = "hz_name"

    @classmethod
    def handle(
        cls,
        value: str,  # noqa: ARG003
        context: CfnginContext,
        *__args: Any,
        **__kwargs: Any,
    ) -> str:
        """Return the name of the private Hosted Zone attached to the vpc.

        This HZ will be used to create CNAME Resource Records for other resources in the
        secondary region.

        """
        return (
            str(context.parameters.get("department")).replace('"', "")
            + "."
            + (context.parameters.get("networking_tier_namespace") or context.namespace)
            + "."
            + str(context.parameters.get("environment")).replace('"', "")
            + ".aws.swacorp.com."
        )
