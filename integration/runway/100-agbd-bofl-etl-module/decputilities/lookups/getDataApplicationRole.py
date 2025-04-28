import logging

from runway.context import CfnginContext
from runway.cfngin.providers.base import BaseProvider
from runway.lookups.handlers.base import LookupHandler
from ccplatcfnginlibs.helpers import cloudformation # pragma: no cover

TYPE_NAME = 'getDataApplicationRole'
LOGGER = logging.getLogger(__name__)

class Lookup(LookupHandler):

    @classmethod
    def handle(cls, value, context: CfnginContext, provider: BaseProvider, **kwargs) -> str:  # pragma: no cover
        """getDataApplicationRole."""
        namespace = context.parameters["decp_namespace"]

        stack_name = namespace + '-app-roles'
        stack_output = 'o' + value.lower() + 'rolearn'

        data_application_role = cls.get_data_application_role(stack_name, stack_output)
        return data_application_role

    @classmethod
    def get_possible_options(cls, stack_name):
        """gets possible options of roles from the stack outputs based on stack name"""
        stack_outputs = cloudformation.get_all_outputs(stack_name)

        outputs = []
        for stack_output in stack_outputs:
            output = stack_output['OutputKey'][1:].replace("rolearn", "")
            outputs.append(output)

        return ', '.join(outputs)

    @classmethod
    def get_data_application_role(cls, stack_name, stack_output):
        """finds data application role arn based on config"""
        try:
            return cloudformation.get_output(
                stack_name,
                stack_output
            )
        except:
            possible_options = cls.get_possible_options(stack_name)
            stack_output = stack_output[1:].replace("rolearn", "")

            LOGGER.error(
                f"Stack {stack_output} doesn't exist. Possible options are {possible_options}")
            raise Exception(
                f"Stack {stack_output} doesn't exist. Possible options are {possible_options}")