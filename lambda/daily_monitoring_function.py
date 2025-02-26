import os
import requests
import boto3
import pandas as pd
from io import StringIO
import datetime
import json

# AWS clients
s3 = boto3.client('s3')
sns = boto3.client('sns')
ssm = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')

# Constants
BUCKET_NAME = os.environ['BUCKET_NAME']
PARAMETER_NAME_NASA = os.environ['NASA_API_PARAMETER_NAME']
PARAMETER_NAME_OPENCAGE = os.environ['OPENCAGE_API_PARAMETER_NAME']
FRP_THRESHOLD = 50  # Minimum Fire Radiative Power (FRP) to trigger alerts
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']  # DynamoDB table name

# DynamoDB Table
subscription_table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Get API Keys from SSM Parameter Store
def get_nasa_api_key():
    response = ssm.get_parameter(Name=PARAMETER_NAME_NASA, WithDecryption=True)
    return response['Parameter']['Value']

def get_opencage_api_key():
    response = ssm.get_parameter(Name=PARAMETER_NAME_OPENCAGE, WithDecryption=True)
    return response['Parameter']['Value']

# Get Coordinates from Zip Code using OpenCage API
def get_coordinates_from_zip(zip_code):
    api_key = get_opencage_api_key()
    url = f"https://api.opencagedata.com/geocode/v1/json?q={zip_code}&key={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if data['results']:
        coords = data['results'][0]['geometry']
        return coords['lat'], coords['lng']
    return None, None

# Fetch All Subscriptions from DynamoDB
def get_all_subscriptions():
    response = subscription_table.scan()
    return response.get('Items', [])

# Send Clustered Alerts to Specific SNS Topic
def cluster_and_alert_fires(nearby_fires, user_email, topic_arn):
    grid_size = 0.0725  # 5 miles in degrees (~0.0725 degrees)
    clusters = {}

    for _, fire in nearby_fires.iterrows():
        lat, lon = fire['latitude'], fire['longitude']
        grid_lat = round(lat / grid_size) * grid_size
        grid_lon = round(lon / grid_size) * grid_size
        grid_key = f"{grid_lat},{grid_lon}"

        if grid_key not in clusters:
            clusters[grid_key] = {
                'centroid': (grid_lat, grid_lon),
                'fires': []
            }
        
        clusters[grid_key]['fires'].append(fire)

    for cluster in clusters.values():
        if cluster['fires']:
            fire = cluster['fires'][0]
            message = (
                f"🔥 Wildfire Alert!\n"
                f"Approximate Location: {cluster['centroid'][0]:.4f}, {cluster['centroid'][1]:.4f}\n"
                f"Number of fires in cluster: {len(cluster['fires'])}\n"
                f"Representative FRP: {fire['frp']} MW\n"
                f"Date: {fire['acq_date']}"
            )
            sns.publish(TopicArn=topic_arn, Message=message, Subject="Clustered Wildfire Alert")
            print(f"Clustered Alert sent: {message}")

# Fetch Wildfire Data and Process Alerts
def fetch_and_process_data(user_lat, user_lon, user_email, zip_code, topic_arn):
    api_key = get_nasa_api_key()
    api_url = f'https://firms.modaps.eosdis.nasa.gov/api/country/csv/{api_key}/MODIS_NRT/USA/1'
    response = requests.get(api_url)
    response.raise_for_status()

    csv_data = StringIO(response.text)
    data = pd.read_csv(csv_data)

    data['frp'] = pd.to_numeric(data['frp'], errors='coerce')
    data = data.dropna(subset=['frp'])

    miles_to_degree = 1.0 / 69.0
    lat_min = user_lat - (100 * miles_to_degree)
    lat_max = user_lat + (100 * miles_to_degree)
    lon_min = user_lon - (100 * miles_to_degree)
    lon_max = user_lon + (100 * miles_to_degree)

    nearby_fires = data[
        (data['latitude'] >= lat_min) &
        (data['latitude'] <= lat_max) &
        (data['longitude'] >= lon_min) &
        (data['longitude'] <= lon_max) &
        (data['frp'] >= FRP_THRESHOLD)
    ]

    if not nearby_fires.empty:
        file_name = f'wildfire_data_{zip_code}.csv'
        s3_key = f"{user_email}/{zip_code}/{file_name}"
        s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=nearby_fires.to_csv(index=False))
        print(f"Filtered data uploaded to S3: {s3_key}")
        cluster_and_alert_fires(nearby_fires, user_email, topic_arn)

# Lambda Handler
def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    if 'source' in event and event['source'] == 'aws.events':
        subscriptions = get_all_subscriptions()
        for subscription in subscriptions:
            zip_code = subscription['zip_code']
            email = subscription['email']
            topic_arn = subscription.get('sns_topic_arn')  # Retrieve the specific SNS topic ARN
            if not topic_arn:
                print(f"No SNS topic ARN found for zip code {zip_code}")
                continue

            user_lat, user_lon = get_coordinates_from_zip(zip_code)
            if user_lat and user_lon:
                fetch_and_process_data(user_lat, user_lon, email, zip_code, topic_arn)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Daily wildfire check completed"})
        }
