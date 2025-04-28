"""Get configuration value.

:Query Syntax: ``<file-pash> <object> <field>``

.. rubric:: Example
.. code-block:: yaml

    lookups:
      configs: ccplatcfnginlibs.lookups.ConfigsLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${configs ${module_config} structured_config desired_var}

Contents of file at ``${module_config}``:

.. code-block:: yaml

    structured_config
      desired_var: success

"""

from __future__ import annotations

from typing import Any, ClassVar

import yaml
from deprecated import deprecated
from runway.lookups.handlers.base import LookupHandler


@deprecated(reason="use the 'ccp' lookup instead")
class ConfigsLookup(LookupHandler[Any]):
    """CFNgin lookup."""

    TYPE_NAME: ClassVar[str] = "configs"

    @classmethod
    def handle(cls, value: str, *__args: Any, **__kwargs: Any) -> str:
        """Get configuration based on inputs."""
        # split passed in values
        values = [x.strip() for x in value.split(" ")]

        config_file = values[0]
        structured_config = values[1]
        desired_var = values[2]

        with open(config_file) as stream:  # noqa: PTH123
            config = yaml.safe_load(stream)

        return config[structured_config][desired_var]
