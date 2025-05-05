import os
import json
import logging
from utils.geolocation_utils import get_coordinates
from utils.wildfire_utils import process_fires
from utils.dynamodb_utils import get_subscriptions

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Retrieve S3 bucket name from environment variables
BUCKET_NAME = os.environ['BUCKET_NAME']

def lambda_handler(event, context):
    logger.info("DailyMonitoringFunction triggered")

    try:
        # Ensure the event is triggered by EventBridge
        if event.get('source') != 'aws.events':
            logger.warning("Invalid event source: %s", event.get('source'))
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid event source"})}

        # Fetch all subscriptions from DynamoDB
        subscriptions = get_subscriptions()
        if not subscriptions:
            logger.info("No subscriptions found in DynamoDB.")
            return {"statusCode": 200, "body": json.dumps({"message": "No subscriptions to process"})}

        logger.info("Found %d subscriptions", len(subscriptions))

        # Process each subscription
        for sub in subscriptions:
            zip_code = sub.get('zip_code')
            email = sub.get('email')
            topic_arn = sub.get('sns_topic_arn')

            if not zip_code or not email:
                logger.warning("Missing zip_code or email in subscription: %s", sub)
                continue

            if not topic_arn:
                logger.warning("No SNS topic for zip_code %s, skipping", zip_code)
                continue

            try:
                coordinates = get_coordinates(zip_code)
                if not coordinates:
                    logger.warning("Could not get coordinates for zip_code: %s", zip_code)
                    continue

                logger.info("Processing fires for zip_code: %s, email: %s", zip_code, email)
                process_fires(
                    lat=coordinates[0],
                    lon=coordinates[1],
                    email=email,
                    zip_code=zip_code,
                    topic_arn=topic_arn,
                    bucket_name=BUCKET_NAME
                )

                logger.info("Finished processing for zip_code: %s", zip_code)

            except Exception as e:
                logger.error("Error processing subscription for zip_code %s: %s", zip_code, str(e), exc_info=True)
                continue

        return {"statusCode": 200, "body": json.dumps({"message": "Daily check completed"})}

    except Exception as e:
        logger.error("Fatal error in lambda_handler: %s", str(e), exc_info=True)
        return {"statusCode": 500, "body": json.dumps({"error": "Internal server error"})}
