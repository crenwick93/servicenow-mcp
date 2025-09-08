import unittest
from unittest.mock import MagicMock, patch

from servicenow_mcp.tools.problem_tools import (
    list_problems,
    get_problem_by_number,
    ListProblemsParams,
    GetProblemByNumberParams,
    search_problems,
    SearchProblemsParams,
)
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig
from servicenow_mcp.auth.auth_manager import AuthManager


class TestProblemTools(unittest.TestCase):

    def setUp(self):
        self.auth_config = AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(username="test", password="test"),
        )

    @patch("requests.get")
    def test_list_problems_success(self, mock_get):
        config = ServerConfig(instance_url="https://dev12345.service-now.com", auth=self.auth_config)
        auth_manager = MagicMock(spec=AuthManager)
        auth_manager.get_headers.return_value = {"Authorization": "Bearer FAKE"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "abc123",
                    "number": "PRB0010001",
                    "short_description": "Email outage",
                    "description": "Users cannot send email",
                    "state": "1",
                    "priority": "1 - Critical",
                    "assigned_to": {"display_value": "Jane Admin"},
                    "category": "Software",
                    "subcategory": "Email",
                    "sys_created_on": "2025-06-25 10:00:00",
                    "sys_updated_on": "2025-06-26 09:00:00",
                }
            ]
        }
        mock_get.return_value = mock_response

        params = ListProblemsParams(limit=5, query="email")
        result = list_problems(config, auth_manager, params)

        self.assertTrue(result["success"])
        self.assertIn("problems", result)
        self.assertEqual(len(result["problems"]), 1)
        self.assertEqual(result["problems"][0]["number"], "PRB0010001")

    @patch("requests.get")
    def test_get_problem_by_number_success(self, mock_get):
        config = ServerConfig(instance_url="https://dev12345.service-now.com", auth=self.auth_config)
        auth_manager = MagicMock(spec=AuthManager)
        auth_manager.get_headers.return_value = {"Authorization": "Bearer FAKE"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "abc123",
                    "number": "PRB0010001",
                    "short_description": "Email outage",
                    "description": "Users cannot send email",
                    "state": "1",
                    "priority": "1 - Critical",
                    "assigned_to": {"display_value": "Jane Admin"},
                    "category": "Software",
                    "subcategory": "Email",
                    "sys_created_on": "2025-06-25 10:00:00",
                    "sys_updated_on": "2025-06-26 09:00:00",
                }
            ]
        }
        mock_get.return_value = mock_response

        params = GetProblemByNumberParams(problem_number="PRB0010001")
        result = get_problem_by_number(config, auth_manager, params)

        self.assertTrue(result["success"])
        self.assertIn("problem", result)
        self.assertEqual(result["problem"]["number"], "PRB0010001")

    @patch("requests.get")
    def test_get_problem_by_number_not_found(self, mock_get):
        config = ServerConfig(instance_url="https://dev12345.service-now.com", auth=self.auth_config)
        auth_manager = MagicMock(spec=AuthManager)
        auth_manager.get_headers.return_value = {"Authorization": "Bearer FAKE"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": []}
        mock_get.return_value = mock_response

        params = GetProblemByNumberParams(problem_number="PRB0099999")
        result = get_problem_by_number(config, auth_manager, params)

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Problem not found: PRB0099999")

    @patch("requests.get")
    def test_search_problems_keywords(self, mock_get):
        config = ServerConfig(instance_url="https://dev12345.service-now.com", auth=self.auth_config)
        auth_manager = MagicMock(spec=AuthManager)
        auth_manager.get_headers.return_value = {"Authorization": "Bearer FAKE"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "abc123",
                    "number": "PRB0010002",
                    "short_description": "Windows update issue",
                    "state": "2",
                    "priority": "3 - Moderate",
                    "sys_created_on": "2025-06-20 10:00:00",
                    "sys_updated_on": "2025-06-21 09:00:00",
                }
            ]
        }
        mock_get.return_value = mock_response

        params = SearchProblemsParams(keywords=["Windows", "update"], limit=3)
        result = search_problems(config, auth_manager, params)

        self.assertTrue(result["success"])
        self.assertIn("problems", result)
        self.assertEqual(result["problems"][0]["number"], "PRB0010002")


if __name__ == "__main__":
    unittest.main()


