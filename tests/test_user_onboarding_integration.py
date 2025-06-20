import sys
import os
import json
from unittest.mock import patch

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "fake-table-name"})
@patch("lambda_functions.user_onboarding_function.lambda_function.subscribe_user_to_topic")
@patch("lambda_functions.user_onboarding_function.lambda_function.save_subscription")
@patch("lambda_functions.user_onboarding_function.lambda_function.get_or_create_sns_topic")
def test_user_onboarding_lambda_handler_success(mock_get_topic, mock_save_sub, mock_subscribe):
    from lambda_functions.user_onboarding_function.lambda_function import lambda_handler

    # Simulate a valid SNS topic ARN being returned for the zip code
    mock_get_topic.return_value = "arn:aws:sns:us-east-1:123456789012:test-topic"

    # Simulate a user submitting their email and zip code through an API Gateway event
    event = {
        "body": '{"email": "test@email.com", "zip_code": "12345"}'
    }
    context = {} # Required by Lambda handler signature

    # Invoke the Lambda handler with the mocked event
    response = lambda_handler(event, context)

    # Ensure the handler responds with a 200 status and expected response body
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Subscription successful!"
    assert body["email"] == "test@email.com"
    assert body["zip_code"] == "12345"

    # Verify that internal helper functions were each called once
    mock_get_topic.assert_called_once_with("12345")
    mock_save_sub.assert_called_once()
    mock_subscribe.assert_called_once()
