import os
import json
import boto3
from datetime import datetime

sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

subscription_table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def store_subscription(email, zip_code):
    subscription_table.put_item(
        Item={
            'email': email,
            'zip_code': zip_code,
            'subscription_date': datetime.now().strftime('%Y-%m-%d')
        }
    )
    print(f"Stored subscription for {email} in DynamoDB")

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    body = json.loads(event.get('body', '{}'))
    zip_code = body.get('zip_code')
    email = body.get('email')

    if zip_code and email:
        store_subscription(email, zip_code)
        sns.subscribe(TopicArn=SNS_TOPIC_ARN, Protocol='email', Endpoint=email)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Subscription successful!"})
        }

    return {
        "statusCode": 400,
        "body": json.dumps({"error": "Invalid input. 'zip_code' and 'email' are required."})
    }
