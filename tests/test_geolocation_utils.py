import sys
import os
from unittest.mock import patch, MagicMock
import pytest

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lambda_functions.utils.geolocation_utils import get_coordinates

@patch.dict(os.environ, {"OPENCAGE_API_PARAMETER_NAME": "/fake/opencage/key"})
@patch("lambda_functions.utils.geolocation_utils.get_opencage_api_key", return_value="fake-key")
@patch("lambda_functions.utils.geolocation_utils.requests.get")
def test_returns_none_for_invalid_zip(mock_requests_get, mock_get_api_key):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_requests_get.return_value = mock_response

    result = get_coordinates("00000")
    assert result is None

@patch.dict(os.environ, {"OPENCAGE_API_PARAMETER_NAME": "/fake/opencage/key"})
@patch("lambda_functions.utils.geolocation_utils.get_opencage_api_key", return_value="fake-key")
@patch("lambda_functions.utils.geolocation_utils.requests.get")
def test_returns_none_on_api_failure(mock_requests_get, mock_get_api_key):
    # Simulate request exception (e.g., timeout)
    mock_requests_get.side_effect = Exception("API call failed")

    result = get_coordinates("90210")
    assert result is None
