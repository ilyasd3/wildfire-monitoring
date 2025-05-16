import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lambda_functions.utils.sns_utils import (
    get_or_create_sns_topic,
    subscribe_user_to_topic,
    send_clustered_alert
)

class TestSubscribeUserToTopic:
    @patch("boto3.client")
    def test_successful_subscription(self, mock_boto_client):
        # Mock the SNS client and its subscribe method
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns
        mock_sns.subscribe.return_value = {"SubscriptionArn": "fake-arn"}

        email = "test@email.com"
        topic_arn = "arn:aws:sns:us-east-1:123456789012:test-topic"

        # Call the function to subscribe the user
        result = subscribe_user_to_topic(email, topic_arn)

        # Ensure subscribe was called with correct parameters
        mock_sns.subscribe.assert_called_once_with(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email
        )
        # Confirm the expected response was returned
        assert result == {"SubscriptionArn": "fake-arn"}

class TestGetOrCreateSNSTopic:
    @patch("boto3.client")
    def test_returns_existing_topic(self, mock_boto_client):
        zip_code = "12345"
        existing_arn = f"arn:aws:sns:us-east-1:123456789012:wildfire-alerts-{zip_code}"
        
        # Mock the paginator to return an existing topic ARN
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Topics": [{"TopicArn": existing_arn}]}]
        mock_sns.get_paginator.return_value = mock_paginator

        # Call the function to retrieve or create the topic
        result = get_or_create_sns_topic(zip_code)

        # Should return the existing ARN and not call create_topic
        assert result == existing_arn
        mock_sns.create_topic.assert_not_called()

    @patch("boto3.client")
    def test_creates_new_topic(self, mock_boto_client):
        zip_code = "12345"
        new_arn = f"arn:aws:sns:us-east-1:123456789012:wildfire-alerts-{zip_code}"
        
        # Mock the paginator to simulate no existing topics
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Topics": []}]
        mock_sns.get_paginator.return_value = mock_paginator
        mock_sns.create_topic.return_value = {"TopicArn": new_arn}

        # Call the function to create a new topic
        result = get_or_create_sns_topic(zip_code)

        # Ensure create_topic is called and the correct ARN is returned
        assert result == new_arn
        mock_sns.create_topic.assert_called_once_with(Name=f"wildfire-alerts-{zip_code}")

class TestSendClusteredAlert:
    @patch("boto3.client")
    def test_publish_called_with_clusters(self, mock_boto_client):
        # Mock the SNS client
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns

        # Sample fire data in a DataFrame
        df = pd.DataFrame({
            "latitude": [34.05, 34.06],
            "longitude": [-118.25, -118.26],
            "frp": [50.0, 55.0],
            "acq_date": [datetime.today().strftime("%Y-%m-%d")] * 2
        })

        email = "test@email.com"
        topic_arn = "arn:aws:sns:us-east-1:123456789012:zip-12345"

        # Call the function to send the alert
        send_clustered_alert(df, email, topic_arn)

        # Ensure SNS publish was called with the correct topic and content
        mock_sns.publish.assert_called_once()
        args, kwargs = mock_sns.publish.call_args
        assert kwargs["TopicArn"] == topic_arn
        assert "🔥 Wildfire Alert!" in kwargs["Message"]

    @patch("boto3.client")
    def test_does_nothing_with_empty_dataframe(self, mock_boto_client):
        # If there is no fire data, SNS publish should not be called
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns

        df = pd.DataFrame()

        # Call the function with empty fire data
        send_clustered_alert(df, "test@email.com", "arn:aws:sns:us-east-1:123456789012:test")

        # Ensure no alert is published
        mock_sns.publish.assert_not_called()
