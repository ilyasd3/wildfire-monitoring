import sys
import os

# Add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock
from lambda_functions.utils.geolocation_utils import get_coordinates

@patch("lambda_functions.utils.geolocation_utils.requests.get")
@patch("lambda_functions.utils.geolocation_utils.get_opencage_api_key")
def test_get_coordinates_success(mock_get_api_key, mock_requests_get):
    # Arrange
    mock_get_api_key.return_value = "fake_api_key"

    # Mock OpenCage API JSON response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "geometry": {
                    "lat": 34.0901,
                    "lng": -118.4065
                }
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_requests_get.return_value = mock_response

    # Act
    result = get_coordinates("90210")

    # Assert
    assert result == (34.0901, -118.4065)
