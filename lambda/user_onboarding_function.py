import os
import json
import boto3
from datetime import datetime

# Initialize AWS clients
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
subscription_table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def save_subscription(email, zip_code, topic_arn):
    """
    Save user subscription details to DynamoDB.
    """
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

def get_or_create_sns_topic(zip_code):
    """
    Find existing SNS topic for zip code or create a new one.
    Returns the topic ARN.
    """
    topic_name = f"wildfire-alerts-{zip_code}"
    
    # Check if SNS topic already exists
    topics = sns.list_topics().get('Topics', [])
    for topic in topics:
        if topic_name in topic['TopicArn']:
            print(f"Found existing SNS topic for zip code {zip_code}")
            return topic['TopicArn']
    
    # Create a new SNS topic if it doesn't already exist
    try:
        response = sns.create_topic(Name=topic_name)
        print(f"Created new SNS topic for zip code {zip_code}")
        return response['TopicArn']
    except Exception as e:
        print(f"Failed to create SNS topic: {str(e)}")
        raise

def subscribe_user_to_topic(email, topic_arn):
    """
    Subscribe user's email to the SNS topic.
    """
    try:
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        print(f"Subscribed {email} to SNS topic")
        return response
    except Exception as e:
        print(f"Failed to subscribe user: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Main handler for user subscription requests.
    Expects POST request with email and zip_code in body.
    """
    print("Processing subscription request...")
    
    try:
        body = json.loads(event.get('body', '{}'))
        zip_code = body.get('zip_code')
        email = body.get('email')

        if not zip_code or not email:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields",
                    "message": "Please provide both email and zip_code"
                })
            }

        # Set up subscription
        topic_arn = get_or_create_sns_topic(zip_code)
        save_subscription(email, zip_code, topic_arn)
        subscribe_user_to_topic(email, topic_arn)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Subscription successful!",
                "email": email,
                "zip_code": zip_code
            })
        }

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }
