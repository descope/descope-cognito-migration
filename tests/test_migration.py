import unittest
from unittest.mock import patch, MagicMock
from src.migration_utils import (
    fetch_cognito_users,
    fetch_cognito_user_groups,
    api_request_with_retry,
)


class TestMigration(unittest.TestCase):
    @patch("src.migration_utils.boto3.client")
    @patch("src.migration_utils.time.sleep", return_value=None)
    def test_fetch_cognito_users(self, mock_sleep, mock_boto_client):
        mock_cognito_client = MagicMock()
        mock_cognito_client.list_users.side_effect = [
            {"Users": [{"Username": "user1"}], "PaginationToken": "token"},
            {"Users": [{"Username": "user2"}]},
        ]
        mock_boto_client.return_value = mock_cognito_client

        users = fetch_cognito_users()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0]["Username"], "user1")
        self.assertEqual(users[1]["Username"], "user2")

    @patch("src.migration_utils.boto3.client")
    @patch("src.migration_utils.time.sleep", return_value=None)
    def test_fetch_cognito_user_groups(self, mock_sleep, mock_boto_client):
        mock_cognito_client = MagicMock()
        mock_cognito_client.list_groups.side_effect = [
            {"Groups": [{"GroupName": "group1"}], "NextToken": "token"},
            {"Groups": [{"GroupName": "group2"}]},
        ]
        mock_boto_client.return_value = mock_cognito_client

        groups = fetch_cognito_user_groups()
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]["GroupName"], "group1")
        self.assertEqual(groups[1]["GroupName"], "group2")


if __name__ == "__main__":
    unittest.main()
