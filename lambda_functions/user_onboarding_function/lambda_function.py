import os
import json
from utils.dynamodb_utils import save_subscription
from utils.sns_utils import get_or_create_sns_topic, subscribe_user_to_topic

def lambda_handler(event, context):
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
