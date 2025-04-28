"""Get a value from the CCP module config file.

:Query Syntax: ``<jsonpath-query>[::<arg>=<arg-val>, ...]``

This hook uses the JSONPath_ syntax to extract values from the module config file.
JSONPath_ was chosen because it is lightweight and it's syntax doesn't interfere with
Runway's lookup syntax.

.. seealso::
  JSONPath Online Evaluator
    https://jsonpath.com/


.. rubric:: Arguments

This Lookup supports all :ref:`Common Lookup Arguments` but,
the following have limited or no effect:

- region


.. rubric:: Example
.. code-block:: yaml

    lookups:
      ccp: ccplatcfnginlibs.lookups.CcpLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${ccp foo[*].bar}

.. _JSONPath: https://goessner.net/articles/JsonPath/

"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import yaml
from jsonpath_ng.ext import parse
from runway.lookups.handlers.base import LookupHandler

if TYPE_CHECKING:
    from runway.context import CfnginContext


class CcpLookup(LookupHandler["CfnginContext"]):
    """CFNgin lookup."""

    TYPE_NAME: ClassVar[str] = "ccp"

    @classmethod
    def handle(
        cls,
        value: str,
        context: CfnginContext,
        *__args: Any,
        **__kwargs: Any,
    ) -> Any:
        """Get a value from the module config file using JSONPath syntax.

        Args:
            value: The JSONPath query and optional arguments.
            context: CFNgin context object.
            provider: AWS provider object.

        """
        query, args = cls.parse(value)
        module_config = yaml.safe_load(
            Path(context.parameters["module_config"]).read_bytes()
        )
        result = [match.value for match in parse(query).find(module_config)]
        if not result:
            if "default" in args:
                return cls.format_results(
                    args.pop("default"),
                    **args,  # pyright: ignore[reportGeneralTypeIssues]
                )
            raise ValueError(f"no results found for query: {query}")
        if len(result) == 1:
            return cls.format_results(
                result[0], **args  # pyright: ignore[reportGeneralTypeIssues]
            )
        return cls.format_results(
            result, **args  # pyright: ignore[reportGeneralTypeIssues]
        )
