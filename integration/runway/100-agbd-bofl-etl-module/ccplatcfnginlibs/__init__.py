"""CCPlat CFNin libs."""

import logging
import os
from importlib.metadata import PackageNotFoundError, version

from . import constants, helpers, hooks, lookups, utils

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    __version__ = "0.0.0"

logging.getLogger(__name__).setLevel(
    logging.DEBUG if os.getenv("DEBUG") else logging.INFO
)

__all__ = [
    "__version__",
    "constants",
    "helpers",
    "hooks",
    "lookups",
    "utils",
]
