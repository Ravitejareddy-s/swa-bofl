import json
import boto3
import teradatasql as tsql


def get_connection(secret_id):
    """ Gets a connection to Teradata using provided secret"""
    ssm_client = boto3.client('secretsmanager', region_name='us-east-1')
    sm_response = ssm_client.get_secret_value(SecretId=secret_id)
    response_json = json.loads(sm_response['SecretString'])
    
    user = response_json['username']
    password = response_json['password']
    host = response_json['host']
    database = response_json['database']
    logmech = response_json.get('logmech', 'TD2')

    connection_options = {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'logmech': logmech
    }

    connection_string = json.dumps(connection_options)

    connection = tsql.connect(connection_string)
    connection.commit()
    connection.autocommit = True
    return connection
