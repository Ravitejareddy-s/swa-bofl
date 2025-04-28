"""Determine SSM Parameter lookup based on the custom namespace if provided.

:Query Syntax: ``<stack-resource-name> stack_name::<parameter-name> <custom-namespace>[ <default>]``

.. deprecated:: 3.0.0

.. rubric:: Example
.. code-block:: yaml

    lookups:
      cx_param_ref: ccplatcfnginlibs.lookups.CxParamRefLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${cx_param_ref vpc vpc::VpcId networking_tier_namespace}
          # this should be used instead
          bar: ${cfn ${default networking_tier_namespace::${namespace}}-vpc.VpcId}

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from botocore.exceptions import ClientError
from deprecated import deprecated
from runway.lookups.handlers.base import LookupHandler

from ..helpers import ssm

if TYPE_CHECKING:
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


@deprecated(reason="use CFNgin's 'cfn' lookup instead")
class CxParamRefLookup(LookupHandler["CfnginContext"]):
    """CFNgin lookup."""

    TYPE_NAME: ClassVar[str] = "cx_param_ref"

    @classmethod
    def handle(
        cls, value: str, context: CfnginContext, *__args: Any, **__kwargs: Any
    ) -> str:
        """Cross namespace SSM parameter lookup."""
        # split passed in values
        values = [x.strip() for x in value.split(" ")]
        default_value = ""

        cls.validate(values)

        stack_resource_name = str(values[0])
        stack_name, param_name = cls.deconstruct(str(values[1]))
        custom_namespace = str(values[2])

        namespace = cls.determine_namespace(context, custom_namespace)

        if len(values) > 3:
            default_value = str(values[3])

        result = None
        try:
            result = ssm.get_stack_parameter(
                stack_resource_name, stack_name, param_name, namespace
            )
            LOGGER.info("%s found: %s", param_name, result)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ParameterNotFound":
                LOGGER.error(
                    "Parameter '%s' in namespace '%s' not found",
                    param_name,
                    namespace,
                )
            else:
                LOGGER.exception(
                    "Unexpected error occurred looking for Parameter '%s' in namespace '%s'",
                    param_name,
                    namespace,
                )
        except Exception:
            LOGGER.exception(
                "Unexpected error occurred looking for Parameter '%s' in namespace '%s'",
                param_name,
                namespace,
            )

        if not result:
            if default_value:
                LOGGER.info(
                    "Param not found in SSM, using default value: %s", default_value
                )
                result = default_value
            else:
                LOGGER.info("Param not found in SSM. No default value provided.")
                raise ValueError(
                    f"Param: {param_name} not found in SSM. No default value provided."
                )

        return result

    @classmethod
    def determine_namespace(cls, context: CfnginContext, custom_namespace: str) -> str:
        """Determine namespace."""
        if custom_namespace in context.parameters:
            namespace = str(context.parameters[custom_namespace])
            LOGGER.info("Using custom namespace: %s", namespace)
            return namespace
        LOGGER.info("Using default namespace: %s", context.namespace)
        return context.namespace

    @classmethod
    def validate(cls, values: Any) -> None:
        """Validate the values."""
        if len(values) < 3:
            raise ValueError(
                "Insufficient number of arguments provided. Required: 3+, Supplied: "
                + str(len(values))
            )

    @classmethod
    def deconstruct(cls, value: str) -> tuple[str, str]:
        """Deconstruct the value."""
        try:
            stack_name, param_name = value.split("::")
        except ValueError:
            raise ValueError(
                f"output handler requires syntax of <stack>::<param_name>.  Got: {value}"
            ) from None

        return stack_name, param_name
