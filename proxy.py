"""Proxy logic for forwarding requests to QuickBooks API."""
import re

import httpx

from auth import token_manager
from config import settings


def is_customers_endpoint(path: str, params: dict | None = None) -> bool:
    """Check if the request path is for Customers entity."""
    # Allow specific customer endpoints (both singular and plural):
    # /v3/company/{realm_id}/customers/{id} or /v3/company/{realm_id}/customer/{id}
    customer_pattern = r"^/v3/company/[^/]+/customers?/[^/]+$"
    if re.match(customer_pattern, path):
        return True
    
    # Allow POST/PUT to /v3/company/{realm_id}/customers or /customer (create/update)
    customer_create_pattern = r"^/v3/company/[^/]+/customers?/?$"
    if re.match(customer_create_pattern, path):
        return True
    
    # Allow query endpoint if it queries Customer entity
    query_pattern = r"^/v3/company/[^/]+/query$"
    if re.match(query_pattern, path) and params:
        query_value = params.get("query", "")
        # Check if the query is for Customer entity
        if query_value and "Customer" in query_value:
            return True
    
    return False


def normalize_path(path: str) -> str:
    """Normalize path to use the hardcoded realm_id from config."""
    # Replace any realm_id in the path with the configured one
    pattern = r"^/v3/company/[^/]+(/.*)$"
    match = re.match(pattern, path)
    if match:
        return f"/v3/company/{settings.QB_REALM_ID}{match.group(1)}"
    return path


async def forward_request(
    method: str,
    path: str,
    headers: dict,
    params: dict | None = None,
    body: bytes | None = None,
) -> tuple[int, dict, bytes]:
    """Forward request to QuickBooks API and return response."""
    # Normalize path to use configured realm_id
    normalized_path = normalize_path(path)

    # Get access token
    access_token = token_manager.get_access_token()
    if not access_token:
        return (
            401,
            {"content-type": "application/json"},
            b'{"error": "Not authenticated. Please check your QB_ACCESS_TOKEN and QB_REFRESH_TOKEN in .env file."}',
        )

    # Build QuickBooks API URL
    qb_url = f"{settings.qb_base_url}{normalized_path}"

    # Prepare headers for QuickBooks API
    qb_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    
    # Only set Content-Type for requests with body (POST, PUT, PATCH)
    if body is not None:
        content_type = headers.get("content-type", "application/json")
        qb_headers["Content-Type"] = content_type

    # Forward request
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=qb_url,
                headers=qb_headers,
                params=params,
                content=body,
                timeout=30.0,
            )

            # Get response body
            response_body = response.content

            # Prepare response headers (exclude hop-by-hop headers and Content-Length)
            # FastAPI will automatically set Content-Length based on the body
            response_headers = {
                key: value
                for key, value in response.headers.items()
                if key.lower()
                not in [
                    "connection",
                    "keep-alive",
                    "transfer-encoding",
                    "upgrade",
                    "proxy-authenticate",
                    "proxy-authorization",
                    "te",
                    "trailer",
                    "content-length",  # Let FastAPI set this automatically
                    "content-encoding",  # May cause issues if body is modified
                ]
            }

            return response.status_code, response_headers, response_body
    except httpx.TimeoutException:
        return (
            504,
            {"content-type": "application/json"},
            b'{"error": "Gateway timeout"}',
        )
    except Exception as e:
        return (
            502,
            {"content-type": "application/json"},
            f'{{"error": "Bad gateway: {str(e)}"}}'.encode(),
        )

