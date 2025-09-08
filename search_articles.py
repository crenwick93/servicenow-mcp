import json
import os
import sys
from typing import List

try:
    # Optional: load .env if python-dotenv is installed
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

from servicenow_mcp.utils.config import (
    ServerConfig,
    AuthConfig,
    AuthType,
    BasicAuthConfig,
    OAuthConfig,
    ApiKeyConfig,
)
from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.knowledge_base import (
    search_articles,
    SearchArticlesParams,
)


def build_auth_config() -> AuthConfig:
    auth_type = (os.getenv("SERVICENOW_AUTH_TYPE") or os.getenv("AUTH_TYPE") or "basic").lower()

    if auth_type == "basic":
        return AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(
                username=os.getenv("SERVICENOW_USERNAME") or os.getenv("USERNAME"),
                password=os.getenv("SERVICENOW_PASSWORD") or os.getenv("PASSWORD"),
            ),
        )

    if auth_type == "oauth":
        return AuthConfig(
            type=AuthType.OAUTH,
            oauth=OAuthConfig(
                client_id=os.getenv("SERVICENOW_CLIENT_ID") or os.getenv("CLIENT_ID"),
                client_secret=os.getenv("SERVICENOW_CLIENT_SECRET") or os.getenv("CLIENT_SECRET"),
                username=os.getenv("SERVICENOW_USERNAME") or os.getenv("USERNAME"),
                password=os.getenv("SERVICENOW_PASSWORD") or os.getenv("PASSWORD"),
                token_url=os.getenv("SERVICENOW_TOKEN_URL"),
            ),
        )

    if auth_type == "api_key":
        return AuthConfig(
            type=AuthType.API_KEY,
            api_key=ApiKeyConfig(
                api_key=os.getenv("SERVICENOW_API_KEY") or os.getenv("API_KEY"),
                header_name=os.getenv("SERVICENOW_API_KEY_HEADER") or "X-ServiceNow-API-Key",
            ),
        )

    raise RuntimeError(f"Unsupported AUTH_TYPE: {auth_type}")


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: python3 search_articles.py <keyword1> [keyword2 ...]", file=sys.stderr)
        return 2

    instance_url = os.getenv("SERVICENOW_INSTANCE_URL") or os.getenv("INSTANCE_URL")
    if not instance_url:
        print("Missing SERVICENOW_INSTANCE_URL (or INSTANCE_URL) in environment.", file=sys.stderr)
        return 2

    auth_config = build_auth_config()
    server_config = ServerConfig(instance_url=instance_url, auth=auth_config, timeout=30)
    auth = AuthManager(server_config.auth, server_config.instance_url)

    keywords = argv[1:]
    result = search_articles(
        server_config,
        auth,
        SearchArticlesParams(keywords=keywords, limit=20, offset=0),
    )

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


