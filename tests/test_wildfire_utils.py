import sys
import os
from unittest.mock import patch, MagicMock
import pandas as pd

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lambda_functions.utils.wildfire_utils import process_fires

MODULE_PATH = "lambda_functions.utils.wildfire_utils"

class TestProcessFires:
    @patch.dict(os.environ, {"NASA_API_PARAMETER_NAME": "/fake/nasa/key"})
    @patch(f"{MODULE_PATH}.send_clustered_alert")
    @patch(f"{MODULE_PATH}.s3")
    @patch(f"{MODULE_PATH}.requests.get")
    @patch(f"{MODULE_PATH}.get_nasa_api_key")
    def test_process_fires_sends_alert_and_saves_to_s3(self, mock_get_api_key, mock_requests_get, mock_s3, mock_send_alert):
        # Mock the NASA API key retrieval
        mock_get_api_key.return_value = "fake-nasa-api-key"

        # Create mock CSV wildfire data with two entries, only one with high FRP
        csv_data = """latitude,longitude,frp,acq_date
34.05,-118.25,60.0,2024-05-01
36.17,-115.14,20.0,2024-05-01
"""

        # Simulate a successful API response with CSV wildfire data
        mock_response = MagicMock()
        mock_response.text = csv_data
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        # Define test input parameters
        test_email = "test@email.com"
        zip_code = "12345"
        topic_arn = "arn:aws:sns:us-east-1:123456789012:test-topic"
        bucket_name = "wildfire-bucket"
        lat, lon = 34.05, -118.25

        # Call the function to process the wildfire data
        process_fires(lat, lon, test_email, zip_code, topic_arn, bucket_name)

        # Check that the NASA API was called
        mock_requests_get.assert_called_once()

        # Verify that the filtered data was saved to S3
        mock_s3.put_object.assert_called_once()
        args, kwargs = mock_s3.put_object.call_args
        assert kwargs["Bucket"] == bucket_name
        assert kwargs["Key"].startswith(f"{test_email}/{zip_code}/wildfire_data_")
        assert "latitude" in kwargs["Body"]

        # Confirm that an alert was sent with the filtered fire data
        mock_send_alert.assert_called_once()
        alert_args, _ = mock_send_alert.call_args
        assert isinstance(alert_args[0], pd.DataFrame)
        assert len(alert_args[0]) == 1  # Only the high FRP fire should be included
