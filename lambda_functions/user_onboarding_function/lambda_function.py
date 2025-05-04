import os
import json
import logging
from utils.dynamodb_utils import save_subscription
from utils.sns_utils import get_or_create_sns_topic, subscribe_user_to_topic

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Processing subscription request...")

    try:
        body = json.loads(event.get("body", "{}"))
        zip_code = body.get("zip_code")
        email = body.get("email")

        if not zip_code or not email:
            logger.warning("Missing required fields: email=%s, zip_code=%s", email, zip_code)
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields",
                    "message": "Please provide both email and zip_code"
                })
            }

        topic_arn = get_or_create_sns_topic(zip_code)
        logger.info("SNS topic ARN for zip code %s: %s", zip_code, topic_arn)

        save_subscription(email, zip_code, topic_arn)
        logger.info("Saved subscription: email=%s, zip_code=%s", email, zip_code)

        subscribe_user_to_topic(email, topic_arn)
        logger.info("Subscribed user to SNS topic: email=%s", email)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Subscription successful!",
                "email": email,
                "zip_code": zip_code
            })
        }

    except Exception as e:
        logger.error("Error processing request: %s", str(e), exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later."
            })
        }
