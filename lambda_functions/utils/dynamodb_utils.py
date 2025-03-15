import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
subscription_table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def save_subscription(email, zip_code, topic_arn):
    """Save user subscription details to DynamoDB."""

    try:
        subscription_table.put_item(
            Item={
                'email': email,
                'zip_code': zip_code,
                'sns_topic_arn': topic_arn,
                'subscription_date': datetime.now().strftime('%Y-%m-%d')
            }
        )
        print(f"Saved subscription for {email} to DynamoDB")
    except Exception as e:
        print(f"Failed to save subscription: {str(e)}")
        raise

def get_subscriptions():
    """Retrieve all active subscriptions from DynamoDB."""

    try:
        response = subscription_table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"Failed to get subscriptions: {str(e)}")
        return []
