import os
import requests
from lambda_functions.utils.ssm_utils import get_opencage_api_key

def get_coordinates(zip_code):
    """Use OpenCage API to convert zip code to (lat, lon) coordinates."""

    if not zip_code or not zip_code.strip():
        raise ValueError("Zip code must not be empty")

    api_key = get_opencage_api_key()
    if not api_key:
        raise ValueError("OpenCage API key is missing")

    try:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={zip_code}&key={api_key}&countrycode=us"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            print(f"No results found for zip code: {zip_code}")
            return None

        geometry = data["results"][0].get("geometry")
        if not geometry or "lat" not in geometry or "lng" not in geometry:
            print(f"Invalid geometry data for zip code: {zip_code}")
            return None

        return geometry["lat"], geometry["lng"]

    except requests.RequestException as e:
        print(f"HTTP error while fetching coordinates for zip {zip_code}: {str(e)}")
        return None

    except Exception as e:
        print(f"Unexpected error while getting coordinates for zip {zip_code}: {str(e)}")
        return None
