"""Validate config using a pydantic model.

:Path: ``ccplatcfnginlibs.hooks.validate_config``

.. rubric:: Example
.. code-block:: yaml

  pre_deploy:
    - path: ccplatcfnginlibs.hooks.validate_config
      args:
        file_path: ${module_config}
        model_class: my_module.models.ModuleConfigModel

"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from runway.utils import load_object_from_string


def validate_config(
    context: object,  # noqa: ARG001
    *__args: object,
    file_path: Path | str,
    model_class: Any,
    **__kwargs: Any,
) -> Any:
    """Validate config using a a pydantic model."""
    if isinstance(model_class, str):
        model_class = load_object_from_string(model_class)
    if not issubclass(model_class, BaseModel):
        raise TypeError(f"{model_class} must be a subclass of pydantic.BaseModel")
    return model_class.model_validate(yaml.safe_load(Path(file_path).read_bytes()))
