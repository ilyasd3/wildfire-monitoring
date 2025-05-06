import os
import requests
import pandas as pd
from io import StringIO
import boto3
from lambda_functions.utils.ssm_utils import get_nasa_api_key
from lambda_functions.utils.sns_utils import send_clustered_alert

s3 = boto3.client('s3')

# Constants for filtering
FRP_THRESHOLD = 50  # Only fires with FRP ≥ 50 will be included
MILES_PER_DEGREE = 69.0  # Approximate miles per degree of latitude
ALERT_RADIUS_MILES = 100  # Search within 100 miles

def process_fires(lat, lon, email, zip_code, topic_arn, bucket_name):
    """Fetch and process wildfire data for a location, filtering based on FRP and 100-mile radius."""

    # Input validation
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        print(f"Invalid latitude/longitude: lat={lat}, lon={lon}")
        return

    if not email or "@" not in email:
        print(f"Invalid email: {email}")
        return

    if not zip_code or not zip_code.strip().isdigit():
        print(f"Invalid zip code: {zip_code}")
        return

    if not topic_arn or not topic_arn.startswith("arn:aws:sns"):
        print(f"Invalid SNS topic ARN: {topic_arn}")
        return

    if not bucket_name:
        print("Bucket name is missing.")
        return

    try:
        api_key = get_nasa_api_key()
        url = f'https://firms.modaps.eosdis.nasa.gov/api/country/csv/{api_key}/MODIS_NRT/USA/1'

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching wildfire data from NASA: {str(e)}")
            return

        if not response.text.strip():
            print("NASA API returned an empty response.")
            return

        try:
            data = pd.read_csv(StringIO(response.text))
        except Exception as e:
            print(f"Error parsing wildfire CSV data: {str(e)}")
            return

        if 'frp' not in data.columns or 'latitude' not in data.columns or 'longitude' not in data.columns:
            print("Missing required columns in NASA data.")
            return

        data['frp'] = pd.to_numeric(data['frp'], errors='coerce')
        data = data.dropna(subset=['frp'])

        # Apply FRP filter
        data = data[data['frp'] >= FRP_THRESHOLD].copy()

        # Calculate bounding box for 100-mile search radius
        miles_to_degrees = 1.0 / MILES_PER_DEGREE
        lat_min = lat - (ALERT_RADIUS_MILES * miles_to_degrees)
        lat_max = lat + (ALERT_RADIUS_MILES * miles_to_degrees)
        lon_min = lon - (ALERT_RADIUS_MILES * miles_to_degrees)
        lon_max = lon + (ALERT_RADIUS_MILES * miles_to_degrees)

        # Filter fires by latitude & longitude
        nearby_fires = data[
            (data['latitude'] >= lat_min) & (data['latitude'] <= lat_max) &
            (data['longitude'] >= lon_min) & (data['longitude'] <= lon_max)
        ]

        print(f"🔥 {len(nearby_fires)} fires found near {zip_code} (within 100 miles, FRP ≥ {FRP_THRESHOLD})")

        if not nearby_fires.empty:
            file_name = f'wildfire_data_{zip_code}.csv'
            s3_key = f"{email}/{zip_code}/{file_name}"

            try:
                s3.put_object(Bucket=bucket_name, Key=s3_key, Body=nearby_fires.to_csv(index=False))
            except Exception as e:
                print(f"Failed to upload file to S3: {str(e)}")
                return

            try:
                send_clustered_alert(nearby_fires, email, topic_arn)
            except Exception as e:
                print(f"Failed to send alert: {str(e)}")
        else:
            print("No fires met the filtering criteria. No alerts sent.")

    except Exception as e:
        print(f"Unexpected error in process_fires for {email}: {str(e)}")
