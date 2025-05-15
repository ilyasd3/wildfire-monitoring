import sys
import os
from unittest.mock import patch

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@patch.dict(os.environ, {"BUCKET_NAME": "fake-bucket", "DYNAMODB_TABLE_NAME": "fake-table"})
@patch("lambda_functions.daily_monitoring_function.lambda_function.get_subscriptions")
@patch("lambda_functions.daily_monitoring_function.lambda_function.get_coordinates")
@patch("lambda_functions.daily_monitoring_function.lambda_function.process_fires")
def test_daily_monitoring_lambda_handler_success(
    mock_process_fires,
    mock_get_coordinates,
    mock_get_subscriptions
):
    from lambda_functions.daily_monitoring_function import lambda_function

    # Arrange
    mock_get_subscriptions.return_value = [{
        "email": "test@email.com",
        "zip_code": "12345",
        "sns_topic_arn": "arn:aws:sns:us-east-1:123456789012:test-topic"
    }]
    mock_get_coordinates.return_value = (34.05, -118.25)

    event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event"
    }

    # Act
    response = lambda_function.lambda_handler(event, {})

    # Assert
    assert response["statusCode"] == 200
    assert "Daily check completed" in response["body"]
    mock_get_subscriptions.assert_called_once()
    mock_get_coordinates.assert_called_once_with("12345")
    mock_process_fires.assert_called_once()
