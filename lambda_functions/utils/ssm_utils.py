import boto3
import os

ssm = boto3.client('ssm')

def get_nasa_api_key():
    """Retrieve NASA API key from SSM Parameter Store."""
    response = ssm.get_parameter(Name=os.environ['NASA_API_PARAMETER_NAME'], WithDecryption=True)
    return response['Parameter']['Value']

def get_opencage_api_key():
    """Retrieve OpenCage API key from SSM Parameter Store."""
    response = ssm.get_parameter(Name=os.environ['OPENCAGE_API_PARAMETER_NAME'], WithDecryption=True)
    return response['Parameter']['Value']
