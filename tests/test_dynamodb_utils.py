import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestSaveSubscription:
    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "fake-table"})
    @patch("lambda_functions.utils.dynamodb_utils.subscription_table")
    def test_successful_save(self, mock_subscription_table):
        # Arrange
        mock_subscription_table.put_item = MagicMock()

        from lambda_functions.utils.dynamodb_utils import save_subscription

        test_email = "test@email.com"
        test_zip = "12345"
        test_topic_arn = "arn:aws:sns:us-east-1:123456789012:zip-12345"

        # Act
        save_subscription(test_email, test_zip, test_topic_arn)

        # Assert
        args, kwargs = mock_subscription_table.put_item.call_args
        item = kwargs["Item"]

        assert item["email"] == test_email
        assert item["zip_code"] == test_zip
        assert item["sns_topic_arn"] == test_topic_arn
        assert "subscription_date" in item
        datetime.strptime(item["subscription_date"], "%Y-%m-%d")
        mock_subscription_table.put_item.assert_called_once()

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "fake-table"})
    @patch("lambda_functions.utils.dynamodb_utils.subscription_table")
    def test_raises_on_invalid_email(self, mock_subscription_table):
        from lambda_functions.utils.dynamodb_utils import save_subscription
        with pytest.raises(ValueError, match="Invalid email"):
            save_subscription("invalidemail", "12345", "arn:aws:sns:us-east-1:123456789012:zip-12345")

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "fake-table"})
    @patch("lambda_functions.utils.dynamodb_utils.subscription_table")
    def test_raises_on_invalid_zip(self, mock_subscription_table):
        from lambda_functions.utils.dynamodb_utils import save_subscription
        with pytest.raises(ValueError, match="Invalid zip code"):
            save_subscription("test@email.com", "notazip", "arn:aws:sns:us-east-1:123456789012:zip-12345")

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "fake-table"})
    @patch("lambda_functions.utils.dynamodb_utils.subscription_table")
    def test_raises_on_invalid_topic_arn(self, mock_subscription_table):
        from lambda_functions.utils.dynamodb_utils import save_subscription
        with pytest.raises(ValueError, match="Invalid SNS topic ARN"):
            save_subscription("test@email.com", "12345", "bad-topic-arn")

class TestGetSubscriptions:
    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "fake-table"})
    @patch("lambda_functions.utils.dynamodb_utils.subscription_table")
    def test_returns_items(self, mock_subscription_table):
        fake_items = [
            {"email": "a@email.com", "zip_code": "54321"},
            {"email": "b@email.com", "zip_code": "12345"}
        ]
        mock_subscription_table.scan.return_value = {"Items": fake_items}

        from lambda_functions.utils.dynamodb_utils import get_subscriptions
        result = get_subscriptions()
        assert result == fake_items
        mock_subscription_table.scan.assert_called_once()

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "fake-table"})
    @patch("lambda_functions.utils.dynamodb_utils.subscription_table")
    def test_returns_empty_list_on_failure(self, mock_subscription_table):
        mock_subscription_table.scan.side_effect = Exception("DynamoDB error")

        from lambda_functions.utils.dynamodb_utils import get_subscriptions
        result = get_subscriptions()
        assert result == []
        mock_subscription_table.scan.assert_called_once()
