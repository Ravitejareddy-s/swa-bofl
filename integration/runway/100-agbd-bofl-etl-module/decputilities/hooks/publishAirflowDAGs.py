"""Publish Airflow DAGs to target MWAA environment S3 location."""
import logging

from runway.context import CfnginContext
from ccplatcfnginlibs.helpers import cloudformation # pragma: no cover
import subprocess

LOGGER = logging.getLogger(__name__)

def hook(provider, context: CfnginContext, **kwargs):
  """
    This hook uploads all DAGs to target MWAA S3 location
    """
  LOGGER.info("Running Pre Build Hook::Uploading DAGs to S3")

  try:
    local_dags_path = kwargs['vLocalDAGsPath']

    namespace = context.parameters["decp_namespace"]
    
    stack_name = namespace + '-mwaa-stack'
    stack_output = 'oMWAADAGLocation'

    s3_dag_location = get_S3_location(stack_name, stack_output)
    
    LOGGER.info(f"Received local DAGs path: {local_dags_path} and target S3 location: {s3_dag_location}")

    """s3 upload"""
    subprocess_cmd(f"aws s3 sync {local_dags_path}/ {s3_dag_location}/")

    LOGGER.info("Uploaded DAGs to S3")
    return True
  except Exception as e:  # pragma: no cover
    LOGGER.error(f"Error running Pre Build Hook to publish MWAA DAGs: [{e}]")
    return False

def get_S3_location(stack_name, output_name):
    """gets MWAA specific output location for DAGs"""
    return cloudformation.get_output(stack_name, output_name)

def subprocess_cmd(command):
  LOGGER.info("subprocess cmd started")
  process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
  proc_stdout = process.communicate()[0].strip()
  LOGGER.info(proc_stdout)
  LOGGER.info("subprocess cmd started")