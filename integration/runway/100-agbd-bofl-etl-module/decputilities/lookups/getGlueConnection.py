import logging

from runway.context import CfnginContext
from runway.cfngin.providers.base import BaseProvider
from runway.lookups.handlers.base import LookupHandler
from ccplatcfnginlibs.helpers import cloudformation # pragma: no cover


TYPE_NAME = 'getGlueConnection'
LOGGER = logging.getLogger(__name__)

class Lookup(LookupHandler):

    @classmethod
    def handle(cls, value, context: CfnginContext, provider: BaseProvider, **kwargs) -> str:  # pragma: no cover
        """getGlueConnection."""
        namespace = context.parameters["decp_namespace"]
        stack_name = namespace + '-glue-connections'
        if not value:
            version = '1a'
            shortName = 'TD'
        else:
            version = value.split(",")[1]
            shortName = value.split(",")[0].upper()
        stack_output = 'oDecpGlueEtl' + shortName +'Connection' + version

        return cls.get_glue_connection(stack_name, stack_output)

    @classmethod
    def get_possible_options(cls, stack_name):
        """gets possible options of connections from the stack outputs based on stack name"""
        stack_outputs = cloudformation.get_all_outputs(stack_name)

        outputs = []
        for stack_output in stack_outputs:
            outputs.append(stack_output['OutputKey'])

        return ', '.join(outputs)

    @classmethod
    def get_glue_connection(cls, stack_name, stack_output):
        """finds glue connection name based on config"""
        try:
            return cloudformation.get_output(
                stack_name,
                stack_output
            )
        except:
            possible_options = cls.get_possible_options(stack_name)

            LOGGER.error(
                f"Stack output {stack_output} doesn't exist. Possible options are {possible_options}")
            raise Exception(
                f"Stack output {stack_output} doesn't exist. Possible options are {possible_options}")