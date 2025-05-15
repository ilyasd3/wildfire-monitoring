import sys
import os
from unittest.mock import patch

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestSSMUtils:
    @patch.dict(os.environ, {"NASA_API_PARAMETER_NAME": "/wildfire/nasa/api_key"})
    @patch("lambda_functions.utils.ssm_utils.ssm")
    def test_get_nasa_api_key(self, mock_ssm):
        # Arrange
        from lambda_functions.utils.ssm_utils import get_nasa_api_key

        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "fake-nasa-key"}
        }

        # Act
        result = get_nasa_api_key()

        # Assert
        mock_ssm.get_parameter.assert_called_once_with(
            Name="/wildfire/nasa/api_key",
            WithDecryption=True
        )
        assert result == "fake-nasa-key"

    @patch.dict(os.environ, {"OPENCAGE_API_PARAMETER_NAME": "/wildfire/opencage/api_key"})
    @patch("lambda_functions.utils.ssm_utils.ssm")
    def test_get_opencage_api_key(self, mock_ssm):
        # Arrange
        from lambda_functions.utils.ssm_utils import get_opencage_api_key

        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "fake-opencage-key"}
        }

        # Act
        result = get_opencage_api_key()

        # Assert
        mock_ssm.get_parameter.assert_called_once_with(
            Name="/wildfire/opencage/api_key",
            WithDecryption=True
        )
        assert result == "fake-opencage-key"
