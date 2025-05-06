import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd

# Add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lambda_functions.utils.sns_utils import (
    subscribe_user_to_topic,
    get_or_create_sns_topic,
    send_clustered_alert
)

class TestSubscribeUserToTopic:
    @patch("lambda_functions.utils.sns_utils.sns")
    def test_successful_subscription(self, mock_sns_client):
        mock_response = {"SubscriptionArn": "fake-arn"}
        mock_sns_client.subscribe.return_value = mock_response

        email = "user@example.com"
        topic_arn = "arn:aws:sns:us-east-1:123456789012:test-topic"
        result = subscribe_user_to_topic(email, topic_arn)

        mock_sns_client.subscribe.assert_called_once_with(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email
        )
        assert result == mock_response

class TestGetOrCreateSNSTopic:
    @patch("lambda_functions.utils.sns_utils.sns")
    def test_returns_existing_topic(self, mock_sns_client):
        zip_code = "90210"
        existing_arn = f"arn:aws:sns:us-east-1:123456789012:wildfire-alerts-{zip_code}"

        # Simulate SNS returning the topic in list_topics
        mock_sns_client.list_topics.return_value = {
            "Topics": [{"TopicArn": existing_arn}]
        }

        # Patch create_topic in case it's wrongly called
        mock_sns_client.create_topic.return_value = {"TopicArn": "should_not_be_called"}

        result = get_or_create_sns_topic(zip_code)

        assert result == existing_arn
        mock_sns_client.create_topic.assert_not_called()

    @patch("lambda_functions.utils.sns_utils.sns")
    def test_creates_new_topic(self, mock_sns_client):
        zip_code = "12345"
        new_arn = f"arn:aws:sns:us-east-1:123456789012:wildfire-alerts-{zip_code}"
        mock_sns_client.list_topics.return_value = {"Topics": []}
        mock_sns_client.create_topic.return_value = {"TopicArn": new_arn}

        result = get_or_create_sns_topic(zip_code)

        assert result == new_arn
        mock_sns_client.create_topic.assert_called_once_with(Name=f"wildfire-alerts-{zip_code}")

class TestSendClusteredAlert:
    @patch("lambda_functions.utils.sns_utils.sns")
    def test_publish_called_with_clusters(self, mock_sns_client):
        data = {
            "latitude": [34.05, 34.06],
            "longitude": [-118.25, -118.26],
            "frp": [50.0, 55.0],
            "acq_date": [datetime.today().strftime("%Y-%m-%d")] * 2
        }
        df = pd.DataFrame(data)

        email = "user@example.com"
        topic_arn = "arn:aws:sns:us-east-1:123456789012:zip-90210"

        send_clustered_alert(df, email, topic_arn)

        mock_sns_client.publish.assert_called_once()
        args, kwargs = mock_sns_client.publish.call_args

        assert kwargs["TopicArn"] == topic_arn
        assert "🔥 Wildfire Alert!" in kwargs["Message"]
        assert kwargs["Subject"] == "🔥 Wildfire Alert"

    @patch("lambda_functions.utils.sns_utils.sns")
    def test_does_nothing_with_empty_dataframe(self, mock_sns_client):
        df = pd.DataFrame()
        send_clustered_alert(df, "user@example.com", "arn:aws:sns:us-east-1:123456789012:test")

        mock_sns_client.publish.assert_not_called()
