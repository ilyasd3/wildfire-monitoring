import os
import json
from utils.geolocation_utils import get_coordinates
from utils.wildfire_utils import process_fires
from utils.dynamodb_utils import get_subscriptions

# Retrieve environment variables
BUCKET_NAME = os.environ['BUCKET_NAME']

def lambda_handler(event, context):
    try:
        # Ensure the event is triggered by EventBridge
        if event.get('source') != 'aws.events':
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid event source"})}

        # Fetch all active subscriptions from DynamoDB
        subscriptions = get_subscriptions()
        if not subscriptions:
            return {"statusCode": 200, "body": json.dumps({"message": "No subscriptions to process"})}

        # Process each subscription
        for sub in subscriptions:
            zip_code = sub['zip_code']
            email = sub['email']
            topic_arn = sub.get('sns_topic_arn')

            if not topic_arn:
                continue  # Skip if no SNS topic found for this zip code

            # Get coordinates for the zip code
            coordinates = get_coordinates(zip_code)
            if coordinates:
                process_fires(coordinates[0], coordinates[1], email, zip_code, topic_arn, BUCKET_NAME)

        return {"statusCode": 200, "body": json.dumps({"message": "Daily check completed"})}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": "Internal server error"})}
