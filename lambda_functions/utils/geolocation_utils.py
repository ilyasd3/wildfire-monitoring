import requests
from lambda_functions.utils.ssm_utils import get_opencage_api_key

def get_coordinates(zip_code):
    """Get latitude/longitude for a zip code using OpenCage API."""

    try:
        api_key = get_opencage_api_key()
        url = f"https://api.opencagedata.com/geocode/v1/json?q={zip_code}&key={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        if not data['results']:
            print(f"No coordinates found for zip {zip_code}")
            return None

        return data['results'][0]['geometry']['lat'], data['results'][0]['geometry']['lng']
    except Exception as e:
        print(f"Failed to get coordinates for {zip_code}: {str(e)}")
        return None
