import os
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig, OAuthConfig, ApiKeyConfig
from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.problem_tools import list_problems, get_problem_by_number, ListProblemsParams, GetProblemByNumberParams
from servicenow_mcp.tools.incident_tools import get_incident_by_number, GetIncidentByNumberParams
from dotenv import load_dotenv; load_dotenv()

instance_url = os.getenv("SERVICENOW_INSTANCE_URL") or os.getenv("INSTANCE_URL")
auth_type = (os.getenv("SERVICENOW_AUTH_TYPE") or os.getenv("AUTH_TYPE") or "basic").lower()
if auth_type == "basic":
    cfg = AuthConfig(type=AuthType.BASIC, basic=BasicAuthConfig(
        username=os.getenv("SERVICENOW_USERNAME") or os.getenv("USERNAME"),
        password=os.getenv("SERVICENOW_PASSWORD") or os.getenv("PASSWORD")))
elif auth_type == "oauth":
    cfg = AuthConfig(type=AuthType.OAUTH, oauth=OAuthConfig(
        client_id=os.getenv("SERVICENOW_CLIENT_ID") or os.getenv("CLIENT_ID"),
        client_secret=os.getenv("SERVICENOW_CLIENT_SECRET") or os.getenv("CLIENT_SECRET"),
        username=os.getenv("SERVICENOW_USERNAME") or os.getenv("USERNAME"),
        password=os.getenv("SERVICENOW_PASSWORD") or os.getenv("PASSWORD"),
        token_url=os.getenv("SERVICENOW_TOKEN_URL")))
elif auth_type == "api_key":
    cfg = AuthConfig(type=AuthType.API_KEY, api_key=ApiKeyConfig(
        api_key=os.getenv("SERVICENOW_API_KEY") or os.getenv("API_KEY"),
        header_name=os.getenv("SERVICENOW_API_KEY_HEADER") or "X-ServiceNow-API-Key"))
else:
    raise RuntimeError(f"Unsupported AUTH_TYPE: {auth_type}")

config = ServerConfig(instance_url=instance_url, auth=cfg, timeout=30)
auth = AuthManager(config.auth, config.instance_url)

print("=== list_problems ===")
print(list_problems(config, auth, ListProblemsParams(limit=5)))

inc = os.getenv("TEST_INCIDENT_NUMBER")
if inc:
    print("=== get_incident_by_number ===")
    print(get_incident_by_number(config, auth, GetIncidentByNumberParams(incident_number=inc)))

prb = os.getenv("TEST_PROBLEM_NUMBER")
if prb:
    print("=== get_problem_by_number ===")
    print(get_problem_by_number(config, auth, GetProblemByNumberParams(problem_number=prb)))