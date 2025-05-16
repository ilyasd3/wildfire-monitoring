import sys
import os
from unittest.mock import patch

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestSSMUtils:
    @patch.dict(os.environ, {"NASA_API_PARAMETER_NAME": "/wildfire/nasa/api_key"})
    @patch("lambda_functions.utils.ssm_utils.ssm")
    def test_get_nasa_api_key(self, mock_ssm):
        # Import the function to be tested
        from lambda_functions.utils.ssm_utils import get_nasa_api_key

        # Mock the SSM get_parameter response
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "fake-nasa-key"}
        }

        # Call the function to retrieve the NASA API key
        result = get_nasa_api_key()

        # Check that the correct SSM parameter was requested with decryption
        mock_ssm.get_parameter.assert_called_once_with(
            Name="/wildfire/nasa/api_key",
            WithDecryption=True
        )

        # Confirm that the returned API key matches the mocked value
        assert result == "fake-nasa-key"

    @patch.dict(os.environ, {"OPENCAGE_API_PARAMETER_NAME": "/wildfire/opencage/api_key"})
    @patch("lambda_functions.utils.ssm_utils.ssm")
    def test_get_opencage_api_key(self, mock_ssm):
        # Import the function to be tested
        from lambda_functions.utils.ssm_utils import get_opencage_api_key

        # Mock the SSM get_parameter response
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "fake-opencage-key"}
        }

        # Call the function to retrieve the OpenCage API key
        result = get_opencage_api_key()

        # Check that the correct SSM parameter was requested with decryption
        mock_ssm.get_parameter.assert_called_once_with(
            Name="/wildfire/opencage/api_key",
            WithDecryption=True
        )

        # Confirm that the returned API key matches the mocked value
        assert result == "fake-opencage-key"
