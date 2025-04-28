"""CFNgin hooks."""

from . import global_params
from ._ccplat_common_hooks import CcplatCommonHooks
from ._configure_cross_region_replication import configure_cross_region_replication
from ._configure_stack_name import configure_stack_name
from ._create_custom_parameters import create_custom_parameters
from ._create_module_ssm_parameters import create_module_ssm_parameters
from ._delete_cross_region_replication_role import delete_cross_region_replication_role
from ._delete_custom_parameters import delete_custom_parameters
from ._delete_module_ssm_parameters import delete_module_ssm_parameters
from ._deploy_lz_artifacts import deploy_lz_artifacts
from ._empty_buckets import empty_buckets
from ._ensure_apigateway_service_role import ensure_apigateway_service_role
from ._ensure_autoscaling_service_role import ensure_autoscaling_service_role
from ._validate_config import validate_config
from ._validate_subnets import validate_subnets
from ._validate_subnets_yaml import validate_subnets_yaml
from ._validate_vpc_version import validate_vpc_version

__all__ = [
    "CcplatCommonHooks",
    "configure_cross_region_replication",
    "configure_stack_name",
    "create_custom_parameters",
    "create_module_ssm_parameters",
    "delete_cross_region_replication_role",
    "delete_custom_parameters",
    "delete_module_ssm_parameters",
    "deploy_lz_artifacts",
    "empty_buckets",
    "ensure_apigateway_service_role",
    "ensure_autoscaling_service_role",
    "global_params",
    "validate_config",
    "validate_subnets",
    "validate_subnets_yaml",
    "validate_vpc_version",
]
