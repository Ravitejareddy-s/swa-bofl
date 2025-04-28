import boto3
import json


def log_if_enabled(logger,msg):
    if logger and logger is not None:
        logger.info(msg)


#Get Redshift connection options to use for connection to the cluster
def get_connection_options(db,secret_id,redshift_temp_dir,logger):
    log_if_enabled(logger, "Getting credentials from Secrets Manager")
    ssm_client = boto3.client('secretsmanager', region_name='us-east-1')
    response = ssm_client.get_secret_value(SecretId=secret_id)
    response_json = json.loads(response['SecretString'])
    use_username = response_json['username']
    use_password = response_json['password']
    use_cluster = response_json['host']
    use_port = response_json['port']
    use_url = 'jdbc:redshift://{0}:{1}/{2}'.format(use_cluster,use_port,db)
    log_if_enabled(logger, "Credentials retrieved for user %s" % use_username)
    log_if_enabled(logger, "URL formatted %s" % use_url)

    connection_options = {
        "url": use_url,
        "user": use_username,
        "password": use_password,
        "database": db,
        "redshiftTmpDir": redshift_temp_dir
    }
 
    return connection_options
