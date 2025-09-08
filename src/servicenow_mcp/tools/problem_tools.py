"""
Problem tools for the ServiceNow MCP server.

This module provides read-only tools for listing and retrieving Problem records
from ServiceNow (table: problem).
"""

import logging
from typing import Optional, List

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class ListProblemsParams(BaseModel):
    """Parameters for listing problems."""

    limit: int = Field(10, description="Maximum number of problems to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[str] = Field(None, description="Filter by problem state")
    assigned_to: Optional[str] = Field(None, description="Filter by assigned user sys_id")
    category: Optional[str] = Field(None, description="Filter by category")
    query: Optional[str] = Field(None, description="Search query across short_description/description")


class GetProblemByNumberParams(BaseModel):
    """Parameters for fetching a problem by its number."""

    problem_number: str = Field(..., description="Problem record number, e.g., PRB0010001")


class SearchProblemsParams(BaseModel):
    """Parameters for keyword-based problem search (any-match)."""

    keywords: List[str] = Field(..., description="Keywords to search in short_description/description")
    limit: int = Field(10, description="Maximum number of problems to return")
    offset: int = Field(0, description="Offset for pagination")


def list_problems(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListProblemsParams,
) -> dict:
    """
    List problem records from ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing problems.

    Returns:
        Dictionary with list of problems and status.
    """
    api_url = f"{config.api_url}/table/problem"

    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }

    filters = []
    if params.state:
        filters.append(f"state={params.state}")
    if params.assigned_to:
        filters.append(f"assigned_to={params.assigned_to}")
    if params.category:
        filters.append(f"category={params.category}")
    if params.query:
        filters.append(f"short_descriptionLIKE{params.query}^ORdescriptionLIKE{params.query}")

    if filters:
        query_params["sysparm_query"] = "^".join(filters)

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        problems = []

        for rec in data.get("result", []):
            assigned_to = rec.get("assigned_to")
            if isinstance(assigned_to, dict):
                assigned_to = assigned_to.get("display_value")

            problems.append(
                {
                    "sys_id": rec.get("sys_id"),
                    "number": rec.get("number"),
                    "short_description": rec.get("short_description"),
                    "description": rec.get("description"),
                    "state": rec.get("state"),
                    "priority": rec.get("priority"),
                    "assigned_to": assigned_to,
                    "category": rec.get("category"),
                    "subcategory": rec.get("subcategory"),
                    "created_on": rec.get("sys_created_on"),
                    "updated_on": rec.get("sys_updated_on"),
                }
            )

        return {
            "success": True,
            "message": f"Found {len(problems)} problems",
            "problems": problems,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list problems: {e}")
        return {
            "success": False,
            "message": f"Failed to list problems: {str(e)}",
            "problems": [],
        }


def get_problem_by_number(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetProblemByNumberParams,
) -> dict:
    """
    Fetch a single problem record from ServiceNow by its number.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for fetching the problem.

    Returns:
        Dictionary with the problem details.
    """
    api_url = f"{config.api_url}/table/problem"

    query_params = {
        "sysparm_query": f"number={params.problem_number}",
        "sysparm_limit": 1,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", [])
        if not result:
            return {
                "success": False,
                "message": f"Problem not found: {params.problem_number}",
            }

        rec = result[0]
        assigned_to = rec.get("assigned_to")
        if isinstance(assigned_to, dict):
            assigned_to = assigned_to.get("display_value")

        problem = {
            "sys_id": rec.get("sys_id"),
            "number": rec.get("number"),
            "short_description": rec.get("short_description"),
            "description": rec.get("description"),
            "state": rec.get("state"),
            "priority": rec.get("priority"),
            "assigned_to": assigned_to,
            "category": rec.get("category"),
            "subcategory": rec.get("subcategory"),
            "created_on": rec.get("sys_created_on"),
            "updated_on": rec.get("sys_updated_on"),
        }

        return {
            "success": True,
            "message": f"Problem {params.problem_number} found",
            "problem": problem,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to fetch problem: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch problem: {str(e)}",
        }


def search_problems(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: SearchProblemsParams,
) -> dict:
    """
    Search problems by any of the provided keywords in short_description or description.

    Returns a compact result set to minimize LLM context usage.
    """
    api_url = f"{config.api_url}/table/problem"

    if not params.keywords:
        return {"success": True, "message": "No keywords provided", "problems": []}

    # Build OR chain across all keywords, searching both fields per keyword
    or_parts: List[str] = []
    for kw in params.keywords:
        if not kw:
            continue
        or_parts.append(f"short_descriptionLIKE{kw}")
        or_parts.append(f"descriptionLIKE{kw}")

    if not or_parts:
        return {"success": True, "message": "No valid keywords", "problems": []}

    # Join with ^OR (ServiceNow encoded query OR operator)
    sysparm_query = "^OR".join(or_parts)

    query_params = {
        "sysparm_query": sysparm_query,
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
        # Return compact fields
        "sysparm_fields": "sys_id,number,short_description,state,priority,sys_created_on,sys_updated_on",
    }

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        problems = []
        for rec in data.get("result", []):
            problems.append(
                {
                    "sys_id": rec.get("sys_id"),
                    "number": rec.get("number"),
                    "short_description": rec.get("short_description"),
                    "state": rec.get("state"),
                    "priority": rec.get("priority"),
                    "created_on": rec.get("sys_created_on"),
                    "updated_on": rec.get("sys_updated_on"),
                }
            )

        return {
            "success": True,
            "message": f"Found {len(problems)} problems matching keywords",
            "problems": problems,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to search problems: {e}")
        return {
            "success": False,
            "message": f"Failed to search problems: {str(e)}",
            "problems": [],
        }


