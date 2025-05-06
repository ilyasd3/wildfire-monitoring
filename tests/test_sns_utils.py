import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lambda_functions.utils.sns_utils import (
    get_or_create_sns_topic,
    subscribe_user_to_topic,
    send_clustered_alert
)

class TestSubscribeUserToTopic:
    @patch("boto3.client")
    def test_successful_subscription(self, mock_boto_client):
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns
        mock_sns.subscribe.return_value = {"SubscriptionArn": "fake-arn"}

        email = "user@example.com"
        topic_arn = "arn:aws:sns:us-east-1:123456789012:test-topic"
        result = subscribe_user_to_topic(email, topic_arn)

        mock_sns.subscribe.assert_called_once_with(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email
        )
        assert result == {"SubscriptionArn": "fake-arn"}

class TestGetOrCreateSNSTopic:
    @patch("boto3.client")
    def test_returns_existing_topic(self, mock_boto_client):
        zip_code = "90210"
        existing_arn = f"arn:aws:sns:us-east-1:123456789012:wildfire-alerts-{zip_code}"
        
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Topics": [{"TopicArn": existing_arn}]}]
        mock_sns.get_paginator.return_value = mock_paginator

        result = get_or_create_sns_topic(zip_code)
        assert result == existing_arn
        mock_sns.create_topic.assert_not_called()

    @patch("boto3.client")
    def test_creates_new_topic(self, mock_boto_client):
        zip_code = "12345"
        new_arn = f"arn:aws:sns:us-east-1:123456789012:wildfire-alerts-{zip_code}"
        
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Topics": []}]
        mock_sns.get_paginator.return_value = mock_paginator
        mock_sns.create_topic.return_value = {"TopicArn": new_arn}

        result = get_or_create_sns_topic(zip_code)
        assert result == new_arn
        mock_sns.create_topic.assert_called_once_with(Name=f"wildfire-alerts-{zip_code}")

class TestSendClusteredAlert:
    @patch("boto3.client")
    def test_publish_called_with_clusters(self, mock_boto_client):
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns

        df = pd.DataFrame({
            "latitude": [34.05, 34.06],
            "longitude": [-118.25, -118.26],
            "frp": [50.0, 55.0],
            "acq_date": [datetime.today().strftime("%Y-%m-%d")] * 2
        })

        email = "user@example.com"
        topic_arn = "arn:aws:sns:us-east-1:123456789012:zip-90210"

        send_clustered_alert(df, email, topic_arn)

        mock_sns.publish.assert_called_once()
        args, kwargs = mock_sns.publish.call_args
        assert kwargs["TopicArn"] == topic_arn
        assert "🔥 Wildfire Alert!" in kwargs["Message"]

    @patch("boto3.client")
    def test_does_nothing_with_empty_dataframe(self, mock_boto_client):
        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns

        df = pd.DataFrame()
        send_clustered_alert(df, "user@example.com", "arn:aws:sns:us-east-1:123456789012:test")

        mock_sns.publish.assert_not_called()
