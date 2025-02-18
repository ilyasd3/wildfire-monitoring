import os
import requests
import boto3
import pandas as pd
from io import StringIO
import datetime

# AWS clients
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Constants
BUCKET_NAME = os.environ['BUCKET_NAME'] # Get bucket name from environment variable
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']  # Get SNS Topic ARN from environment variable
API_URL = 'https://firms.modaps.eosdis.nasa.gov/api/country/csv/843c3fa84152e7ce28481acc305ed566/VIIRS_SNPP_NRT/USA/1'  # Replace YOUR_API_KEY
LAT_MIN, LAT_MAX = 32.5, 42.0  # California latitude range
LON_MIN, LON_MAX = -124.4, -114.1  # California longitude range
FRP_THRESHOLD = 50  # Minimum FRP value to trigger alerts

def fetch_and_process_data():
    try:
        # Fetch data from NASA FIRMS API
        response = requests.get(API_URL)
        response.raise_for_status()

        # Read the CSV data into a pandas DataFrame
        csv_data = StringIO(response.text)
        data = pd.read_csv(csv_data)

        # Filter data for California
        data['frp'] = pd.to_numeric(data['frp'], errors='coerce')  # Convert FRP to numeric and handle errors
        data = data.dropna(subset=['frp'])  # Drop rows where FRP is NaN
        california_fires = data[
            (data['latitude'] >= LAT_MIN) & 
            (data['latitude'] <= LAT_MAX) & 
            (data['longitude'] >= LON_MIN) & 
            (data['longitude'] <= LON_MAX) & 
            (data['frp'] >= FRP_THRESHOLD)  # Filter for fires with FRP above the threshold
        ]

        # Save filtered data to S3
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f'california_wildfire_data_{timestamp}.csv'  # Updated file name to reflect California
        s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=california_fires.to_csv(index=False))
        print(f"Filtered data uploaded to S3: {file_name}")

        # Send alerts for high-FRP wildfires in California
        for _, fire in california_fires.iterrows():
            message = (
                f"🔥 Wildfire Alert for California!\n"
                f"Location: {fire['latitude']}, {fire['longitude']}\n"
                f"FRP: {fire['frp']} MW\n"
                f"Date: {fire['acq_date']}"
            )
            sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject="California Wildfire Alert")
            print(f"Alert sent: {message}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")  # Handle HTTP request errors
    except Exception as e:
        print(f"Error: {e}")  # Handle other exceptions

# Lambda handler
def lambda_handler(event, context):
    fetch_and_process_data()
    return {"statusCode": 200, "body": "Wildfire monitoring task completed"}
