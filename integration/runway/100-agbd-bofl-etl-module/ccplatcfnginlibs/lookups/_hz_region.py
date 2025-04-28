"""Get Hosted Zone region.

:Query Syntax: ``<hosted-zone-id>``

This is often used in tandem with ``hz_id`` to get the region of a the Hosted Zone it returns.

.. rubric:: Example
.. code-block:: yaml

    lookups:
      hz_id: ccplatcfnginlibs.lookups.HzIdLookup
      hz_name: ccplatcfnginlibs.lookups.HzNameLookup
      hz_region: ccplatcfnginlibs.lookups.HzRegionLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${hz_region ${hz_id ${hz_name }}}

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from runway.lookups.handlers.base import LookupHandler

if TYPE_CHECKING:
    from runway.context import CfnginContext


class HzRegionLookup(LookupHandler["CfnginContext"]):  # TODO(kyle): refactor
    """Lookup Hosted Zone region."""

    TYPE_NAME: ClassVar[str] = "hz_region"

    @classmethod
    def handle(
        cls, value: str, context: CfnginContext, *__args: Any, **__kwargs: Any
    ) -> str:
        """Return the CCP:Region tag of the private Hosted Zone.

        Raises:
            ValueError: 'CCP:Region' tag not found for Hosted Zone.

        """
        hz_id, _args = cls.parse(value)
        try:
            return next(
                tag
                for tag in context.get_session()
                .client("route53")
                .list_tags_for_resource(ResourceType="hostedzone", ResourceId=hz_id)[
                    "ResourceTagSet"
                ]
                .get("Tags", [])
                if tag.get("Key") == "CCP:Region" and "Value" in tag
            )["Value"]
        except StopIteration as exc:
            raise ValueError(
                f"'CCP:Region' tag not found for Hosted Zone: {hz_id}"
            ) from exc
