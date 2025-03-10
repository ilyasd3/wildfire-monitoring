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

# Environment variables
BUCKET_NAME = os.environ['BUCKET_NAME']
NASA_API_PARAMETER_NAME = os.environ['NASA_API_PARAMETER_NAME']
OPENCAGE_API_PARAMETER_NAME = os.environ['OPENCAGE_API_PARAMETER_NAME']
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']

# Constants
FRP_THRESHOLD = 50  # Minimum FRP to trigger alerts
ALERT_RADIUS_MILES = 100  # How far to look for fires
MILES_PER_DEGREE = 69.0  # Approximate miles per degree of latitude
GRID_SIZE = 0.0725  # ~5 miles in degrees for clustering

# Initialize DynamoDB table
subscription_table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Get API Keys from SSM Parameter Store
def get_nasa_api_key():
    response = ssm.get_parameter(Name=NASA_API_PARAMETER_NAME, WithDecryption=True)
    return response['Parameter']['Value']

def get_opencage_api_key():
    response = ssm.get_parameter(Name=OPENCAGE_API_PARAMETER_NAME, WithDecryption=True)
    return response['Parameter']['Value']

def get_coordinates(zip_code):
    """Get lat/lon for a zip code using OpenCage API."""
    try:
        api_key = get_opencage_api_key()
        url = f"https://api.opencagedata.com/geocode/v1/json?q={zip_code}&key={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        if not data['results']:
            print(f"No coordinates found for zip {zip_code}")
            return None
            
        coordinates = data['results'][0]['geometry']
        return coordinates['lat'], coordinates['lng']
    except Exception as e:
        print(f"Failed to get coordinates for {zip_code}: {str(e)}")
        return None

def get_subscriptions():
    """Get all active subscriptions from DynamoDB."""
    try:
        response = subscription_table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"Failed to get subscriptions: {str(e)}")
        return []

def send_clustered_alert(fires, email, topic_arn):
    """Group nearby fires and send alerts for each cluster."""
    clusters = {}
    
    # Group fires into 5-mile grid cells
    for _, fire in fires.iterrows():
        lat, lon = fire['latitude'], fire['longitude']
        grid_lat = round(lat / GRID_SIZE) * GRID_SIZE
        grid_lon = round(lon / GRID_SIZE) * GRID_SIZE
        grid_key = f"{grid_lat},{grid_lon}"
        
        if grid_key not in clusters:
            clusters[grid_key] = {
                'center': (grid_lat, grid_lon),
                'fires': []
            }
        clusters[grid_key]['fires'].append(fire)
    
    # Send alert for each cluster
    for cluster in clusters.values():
        if not cluster['fires']:
            continue
            
        fire = cluster['fires'][0]  # Use first fire as representative
        message = (
            f"🔥 Wildfire Alert!\n"
            f"Location: {cluster['center'][0]:.4f}, {cluster['center'][1]:.4f}\n"
            f"Number of fires in cluster: {len(cluster['fires'])}\n"
            f"Fire Radiative Power: {fire['frp']} MW\n"
            f"Date: {fire['acq_date']}"
        )
        
        try:
            sns.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject="Wildfire Alert"
            )
            print(f"Sent alert for {email}: {message}")
        except Exception as e:
            print(f"Failed to send alert to {email}: {str(e)}")

def process_fires(lat, lon, email, zip_code, topic_arn):
    """Fetch and process wildfire data for a location."""
    try:
        # Get NASA API key
        api_key = get_nasa_api_key()
        
        # Fetch latest fire data
        url = f'https://firms.modaps.eosdis.nasa.gov/api/country/csv/{api_key}/MODIS_NRT/USA/1'
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse CSV data
        data = pd.read_csv(StringIO(response.text))
        data['frp'] = pd.to_numeric(data['frp'], errors='coerce')
        data = data.dropna(subset=['frp'])
        
        # Calculate search area
        miles_to_degree = 1.0 / MILES_PER_DEGREE
        lat_min = lat - (ALERT_RADIUS_MILES * miles_to_degree)
        lat_max = lat + (ALERT_RADIUS_MILES * miles_to_degree)
        lon_min = lon - (ALERT_RADIUS_MILES * miles_to_degree)
        lon_max = lon + (ALERT_RADIUS_MILES * miles_to_degree)
        
        # Filter nearby fires
        nearby = data[
            (data['latitude'] >= lat_min) &
            (data['latitude'] <= lat_max) &
            (data['longitude'] >= lon_min) &
            (data['longitude'] <= lon_max) &
            (data['frp'] >= FRP_THRESHOLD)
        ]
        
        if not nearby.empty:
            # Save to S3 for record keeping
            file_name = f'fires_{zip_code}_{datetime.datetime.now().strftime("%Y%m%d")}.csv'
            s3_key = f"{email}/{zip_code}/{file_name}"
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=nearby.to_csv(index=False)
            )
            print(f"Saved fire data to S3: {s3_key}")
            
            # Send alerts if needed
            send_clustered_alert(nearby, email, topic_arn)
            
    except Exception as e:
        print(f"Failed to process fires for {email}: {str(e)}")

def lambda_handler(event, context):
    """Main handler for daily wildfire monitoring."""
    print("Starting daily wildfire check...")
    
    try:
        # Only process if triggered by EventBridge
        if 'source' not in event or event['source'] != 'aws.events':
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid event source"})
            }
        
        # Get all subscriptions
        subscriptions = get_subscriptions()
        if not subscriptions:
            print("No active subscriptions found")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No subscriptions to process"})
            }
        
        # Process each subscription
        for sub in subscriptions:
            zip_code = sub['zip_code']
            email = sub['email']
            topic_arn = sub.get('sns_topic_arn')
            
            if not topic_arn:
                print(f"No SNS topic found for zip code {zip_code}")
                continue
                
            coordinates = get_coordinates(zip_code)
            if coordinates:
                process_fires(coordinates[0], coordinates[1], email, zip_code, topic_arn)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Daily check completed"})
        }
        
    except Exception as e:
        print(f"Lambda execution failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
