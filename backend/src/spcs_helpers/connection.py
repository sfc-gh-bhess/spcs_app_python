import os
import snowflake.connector
from snowflake.snowpark import Session

def get_params():
    config = {}
    config['host'] = os.getenv('SNOWFLAKE_HOST')
    config['port'] = os.getenv('SNOWFLAKE_PORT')
    config['protocol'] = 'https'
    config['account'] = os.getenv('SNOWFLAKE_ACCOUNT')
    config['database'] = os.getenv('SNOWFLAKE_DATABASE')
    config['schema'] = os.getenv('SNOWFLAKE_SCHEMA')

    config['warehouse'] = os.getenv('SNOWFLAKE_WAREHOUSE')
    config['user'] = os.getenv('SNOWFLAKE_USER')
    config['password'] = os.getenv('SNOWFLAKE_PASSWORD')
    return config

def get_token():
    with open('/snowflake/session/token', 'r') as f:
        return f.read()

def connection() -> snowflake.connector.SnowflakeConnection:
    args = get_params()
    if args['user']:
        creds = {
            'account': args['account'],
            'user': args['user'],
            'password': args['password'],
            'warehouse': args['warehouse'],
            'database': args['database'],
            'schema': args['schema'],
            'client_session_keep_alive': True
        }
    else:
        token = get_token()
        creds = {
            'host': args['host'],
            'port': args['port'],
            'protocol': args['protocol'],
            'account': args['account'],
            'authenticator': "oauth",
            'token': token,
            'warehouse': args['warehouse'],
            'database': args['database'],
            'schema': args['schema'],
            'client_session_keep_alive': True
        }

    connection = snowflake.connector.connect(**creds)
    return connection

def session() -> Session:
    return Session.builder.configs({"connection": connection()}).create()
