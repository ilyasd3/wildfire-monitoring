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

# Constants
BUCKET_NAME = os.environ['BUCKET_NAME']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
PARAMETER_NAME_NASA = os.environ['NASA_API_PARAMETER_NAME']
PARAMETER_NAME_OPENCAGE = os.environ['OPENCAGE_API_PARAMETER_NAME']
FRP_THRESHOLD = 50  # Minimum Fire Radiative Power (FRP) to trigger alerts

# Function to get the NASA API key securely from SSM Parameter Store
def get_nasa_api_key():
    try:
        response = ssm.get_parameter(Name=PARAMETER_NAME_NASA, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error retrieving NASA API key from SSM Parameter Store: {e}")
        return None

# Function to get the OpenCage API key securely from SSM Parameter Store
def get_opencage_api_key():
    try:
        response = ssm.get_parameter(Name=PARAMETER_NAME_OPENCAGE, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error retrieving OpenCage API key from SSM Parameter Store: {e}")
        return None

# Function to convert zip code to latitude and longitude using OpenCage API
def get_coordinates_from_zip(zip_code):
    try:
        api_key = get_opencage_api_key()
        if not api_key:
            print("OpenCage API key not available")
            return None, None

        url = f"https://api.opencagedata.com/geocode/v1/json?q={zip_code}&key={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data['results']:
            coords = data['results'][0]['geometry']
            return coords['lat'], coords['lng']
        else:
            print(f"No results found for zip code {zip_code}")
            return None, None
    except Exception as e:
        print(f"Error in geocoding API: {e}")
        return None, None

# Function to cluster nearby wildfires using a grid-based approach
def cluster_and_alert_fires(nearby_fires, user_email):
    grid_size = 0.0725  # 5 miles in degrees (~0.0725 degrees)
    clusters = {}

    for _, fire in nearby_fires.iterrows():
        lat, lon = fire['latitude'], fire['longitude']
        
        # Calculate grid cell coordinates
        grid_lat = round(lat / grid_size) * grid_size
        grid_lon = round(lon / grid_size) * grid_size
        grid_key = f"{grid_lat},{grid_lon}"

        # Add fire to the appropriate cluster
        if grid_key not in clusters:
            clusters[grid_key] = {
                'centroid': (grid_lat, grid_lon),
                'fires': []
            }
        
        clusters[grid_key]['fires'].append(fire)

    # Send one alert per cluster
    for cluster in clusters.values():
        if cluster['fires']:
            fire = cluster['fires'][0]  # Use the first fire as a representative
            message = (
                f"🔥 Wildfire Alert!\n"
                f"Approximate Location: {cluster['centroid'][0]:.4f}, {cluster['centroid'][1]:.4f}\n"
                f"Number of fires in cluster: {len(cluster['fires'])}\n"
                f"Representative FRP: {fire['frp']} MW\n"
                f"Date: {fire['acq_date']}"
            )
            sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject="Clustered Wildfire Alert")
            print(f"Clustered Alert sent: {message}")

# Function to fetch wildfire data and process it for alerts within a 100-mile square
def fetch_and_process_data(user_lat, user_lon, user_email):
    try:
        api_key = get_nasa_api_key()
        if not api_key:
            print("NASA API key not available")
            return

        # Fetch wildfire data from NASA FIRMS API
        api_url = f'https://firms.modaps.eosdis.nasa.gov/api/country/csv/{api_key}/MODIS_NRT/USA/1'
        response = requests.get(api_url)
        response.raise_for_status()

        csv_data = StringIO(response.text)
        data = pd.read_csv(csv_data)

        data['frp'] = pd.to_numeric(data['frp'], errors='coerce')
        data = data.dropna(subset=['frp'])

        # Define the 100-mile bounding box
        miles_to_degree = 1.0 / 69.0
        lat_min = user_lat - (100 * miles_to_degree)
        lat_max = user_lat + (100 * miles_to_degree)
        lon_min = user_lon - (100 * miles_to_degree)
        lon_max = user_lon + (100 * miles_to_degree)

        # Filter wildfires within the bounding box
        nearby_fires = data[
            (data['latitude'] >= lat_min) &
            (data['latitude'] <= lat_max) &
            (data['longitude'] >= lon_min) &
            (data['longitude'] <= lon_max) &
            (data['frp'] >= FRP_THRESHOLD)
        ]

        if not nearby_fires.empty:
            cluster_and_alert_fires(nearby_fires, user_email)
        else:
            print("No wildfires found within the specified area.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except Exception as e:
        print(f"Error: {e}")

# Lambda handler function
def lambda_handler(event, context):
    print("Received event:", json.dumps(event))  # Log the entire event for debugging

    try:
        body = event.get('body')
        if isinstance(body, str):
            body = json.loads(body)

        zip_code = body.get('zip_code')
        user_email = body.get('email')

        print(f"Received event with zip code: {zip_code} and email: {user_email}")

        if not zip_code or not user_email:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Invalid input. 'zip_code' and 'email' are required."})
            }

        user_lat, user_lon = get_coordinates_from_zip(zip_code)
        if user_lat is None or user_lon is None:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Invalid zip code"})
            }

        fetch_and_process_data(user_lat, user_lon, user_email)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Wildfire monitoring task completed"})
        }

    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }
