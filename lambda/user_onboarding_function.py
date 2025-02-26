import os
import json
import boto3
from datetime import datetime

sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']

subscription_table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def store_subscription(email, zip_code, topic_arn):
    subscription_table.put_item(
        Item={
            'email': email,
            'zip_code': zip_code,
            'sns_topic_arn': topic_arn,
            'subscription_date': datetime.now().strftime('%Y-%m-%d')
        }
    )
    print(f"Stored subscription for {email} with topic {topic_arn} in DynamoDB")

def create_or_get_sns_topic(zip_code):
    topic_name = f"wildfire-alerts-{zip_code}"
    # Check if the topic already exists
    existing_topics = sns.list_topics().get('Topics', [])
    for topic in existing_topics:
        if topic_name in topic['TopicArn']:
            print(f"Found existing SNS topic for zip code {zip_code}: {topic['TopicArn']}")
            return topic['TopicArn']
    
    # Create a new SNS topic if not found
    response = sns.create_topic(Name=topic_name)
    print(f"Created new SNS topic for zip code {zip_code}: {response['TopicArn']}")
    return response['TopicArn']

def subscribe_user_to_topic(email, topic_arn):
    response = sns.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=email
    )
    print(f"Subscribed {email} to SNS topic {topic_arn}")
    return response

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    body = json.loads(event.get('body', '{}'))
    zip_code = body.get('zip_code')
    email = body.get('email')

    if zip_code and email:
        # Create or get the SNS topic for the specific zip code
        topic_arn = create_or_get_sns_topic(zip_code)
        
        # Store the subscription in DynamoDB
        store_subscription(email, zip_code, topic_arn)
        
        # Subscribe the user to the SNS topic
        subscribe_user_to_topic(email, topic_arn)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Subscription successful!"})
        }

    return {
        "statusCode": 400,
        "body": json.dumps({"error": "Invalid input. 'zip_code' and 'email' are required."})
    }
