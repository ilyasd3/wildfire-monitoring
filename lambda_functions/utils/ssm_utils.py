import boto3
import os
import botocore.exceptions

ssm = boto3.client('ssm')

def get_parameter(name):
    """Retrieve a parameter from AWS SSM with decryption and error handling."""
    if not name:
        raise ValueError("SSM parameter name must be provided")

    try:
        response = ssm.get_parameter(Name=name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except botocore.exceptions.ClientError as e:
        print(f"Failed to retrieve SSM parameter '{name}': {e}")
        raise
    except Exception as e:
        print(f"Unexpected error retrieving SSM parameter '{name}': {e}")
        raise

def get_nasa_api_key():
    name = os.environ.get("NASA_API_PARAMETER_NAME")
    if not name:
        raise EnvironmentError("Missing NASA_API_PARAMETER_NAME environment variable")
    return get_parameter(name)

def get_opencage_api_key():
    name = os.environ.get("OPENCAGE_API_PARAMETER_NAME")
    if not name:
        raise EnvironmentError("Missing OPENCAGE_API_PARAMETER_NAME environment variable")
    return get_parameter(name)
