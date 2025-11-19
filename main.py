"""Main FastAPI application for QuickBooks Proxy API."""
from fastapi import FastAPI, Request, Response, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from config import settings
from proxy import forward_request, is_customers_endpoint

security = HTTPBearer(auto_error=False)

app = FastAPI(
    title="QuickBooks Proxy API",
    description="Proxy API for Intuit QuickBooks that only allows Customers entity endpoints",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_bearer_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Verify bearer token for proxy API authentication."""
    if not settings.PROXY_BEARER_TOKEN:
        # If no token is configured, allow all requests (backward compatibility)
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.credentials != settings.PROXY_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


@app.get("/health")
async def health_check():
    """Health check endpoint (no authentication required)."""
    return {"status": "healthy", "realm_id": settings.QB_REALM_ID}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_request(
    path: str,
    request: Request,
    _: bool = Depends(verify_bearer_token),
):
    """Proxy requests to QuickBooks API (only Customers entity allowed)."""
    # Ensure path starts with /
    if not path.startswith("/"):
        path = f"/{path}"

    # Get query parameters
    params = dict(request.query_params)
    
    # Check if this is a Customers endpoint
    if not is_customers_endpoint(path, params):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Access denied. Only Customers entity endpoints are allowed."},
        )

    # Get request body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()

    # Get request headers
    headers = dict(request.headers)

    # Forward request to QuickBooks API
    status_code, response_headers, response_body = await forward_request(
        method=request.method,
        path=path,
        headers=headers,
        params=params if params else None,
        body=body,
    )

    # Return response
    response = Response(
        content=response_body,
        status_code=status_code,
        headers=response_headers,
    )
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.PROXY_PORT)
