"""Dictionary of Key/Value Stack Outputs.

:Query Syntax: ``<stack-name>``

..deprecated:: 3.0.0

.. rubric:: Example
.. code-block:: yaml

    lookups:
      stack_outputs: ccplatcfnginlibs.lookups.StackOutputsLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${stack_outputs stack-name}

"""

# TODO(kyle): replace use of this lookup with builtin `cfn` lookup
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from deprecated import deprecated
from runway.lookups.handlers.base import LookupHandler

if TYPE_CHECKING:
    from runway.cfngin.providers.aws.default import Provider
    from runway.context import CfnginContext


@deprecated(reason="use CFNgin's 'cfn' lookup instead")
class StackOutputsLookup(LookupHandler["CfnginContext"]):
    """CFNgin lookup."""

    TYPE_NAME: ClassVar[str] = "stack_outputs"

    @classmethod
    def handle(
        cls,
        value: str,
        context: CfnginContext,
        *__args: Any,
        provider: Provider,
        **__kwargs: Any,
    ) -> dict[str, str]:
        """Get stack outputs for a given stack."""
        return provider.get_outputs(cls.resolve_stackname(value, context))

    @classmethod
    def resolve_stackname(cls, value: str, context: CfnginContext) -> str:
        """Resolve stack name.

        Separate method for name resolution in the case
        other developers have specific use cases for formulating stack names
        (like in the case of Public API GW).

        Instead of copying handle() and editing specific lines, they
        can just override this method and use their own logic.

        """
        stack_name = value.strip()

        if "stack_postfix" in context.parameters:
            return f"{context.namespace}-{stack_name}-{context.parameters['stack_postfix']}"

        return f"{context.namespace}-{stack_name}"
