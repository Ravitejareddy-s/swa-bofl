"""Return CIDRs for subnet IDs.

:Query Syntax: ``<subnet-id>[,...]``

.. rubric:: Example
.. code-block:: yaml

    lookups:
      subnet_cidrs: ccplatcfnginlibs.lookups.SubnetCidrsLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${subnet_cidrs subnet-123,${output some-stack.subnet-id}}

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from runway.lookups.handlers.base import LookupHandler

if TYPE_CHECKING:
    from runway.context import CfnginContext


class SubnetCidrsLookup(LookupHandler["CfnginContext"]):
    """CFNgin lookup."""

    TYPE_NAME: ClassVar[str] = "subnet_cidrs"

    @classmethod
    def handle(
        cls, value: str, context: CfnginContext, *__args: Any, **__kwargs: Any
    ) -> str:
        """Return CIDRs for subnet IDs."""
        query, _args = cls.parse(value)

        if not query:
            return ""

        return ",".join(
            subnet["CidrBlock"]
            for subnet in context.get_session()
            .client("ec2")
            .describe_subnets(SubnetIds=query.split(","))["Subnets"]
            if "CidrBlock" in subnet
        )
