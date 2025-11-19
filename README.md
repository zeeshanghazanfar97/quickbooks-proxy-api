# QuickBooks Proxy API

A secure proxy API for Intuit QuickBooks that restricts access to only the Customers entity endpoints. The proxy uses hardcoded QuickBooks account credentials and forwards allowed requests to the QuickBooks API while maintaining the exact same API schema.

## Features

- **Hardcoded Authentication**: Uses your QuickBooks account credentials from environment variables
- **Entity Filtering**: Only allows Customers entity endpoints (`/v3/company/{realm_id}/customers/*`)
- **Automatic Token Refresh**: Handles token refresh automatically before expiration
- **Environment Support**: Works with both sandbox and production QuickBooks environments
- **Same API Schema**: Maintains exact compatibility with QuickBooks API

## Prerequisites

- Python 3.11 or higher
- Intuit Developer account with a registered app
- QuickBooks OAuth2 credentials (Client ID and Client Secret)
- QuickBooks account access token, refresh token, and realm ID (Company ID)

## Installation

### Option 1: Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd quickbooks-proxy
```

2. Create your `.env` file:
```bash
cp .env.example .env
# Edit .env with your QuickBooks credentials
```

3. Build and run with Docker Compose:
```bash
docker-compose up -d
```

Or build and run with Docker directly:
```bash
# Build the image
docker build -t quickbooks-proxy .

# Run the container
docker run -d \
  --name quickbooks-proxy \
  -p 8000:8000 \
  --env-file .env \
  quickbooks-proxy
```

### Option 2: Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd quickbooks-proxy
```

2. Install dependencies:
```bash
pip install -e .
```

Or using uv:
```bash
uv pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Get your QuickBooks OAuth2 credentials:
   - Go to [Intuit Developer Portal](https://developer.intuit.com/app/developer/dashboard)
   - Create a new app or use an existing one
   - Navigate to "Keys & OAuth" section
   - Copy your **Client ID** and **Client Secret**

3. Get your QuickBooks Access Token, Refresh Token, and Realm ID:
   
   **Option A: Using Intuit OAuth Playground (Recommended)**
   - Go to [Intuit OAuth Playground](https://developer.intuit.com/app/developer/playground)
   - Select your app and environment (sandbox/production)
   - Click "Get App Now" and authorize the app
   - Copy the `access_token`, `refresh_token`, and `realmId` from the response

   **Option B: Using OAuth Flow Script**
   - You can use any OAuth2 tool or script to complete the OAuth flow
   - The response will contain `access_token`, `refresh_token`, and `realmId`

4. Configure your `.env` file:
```env
QB_CLIENT_ID=your_client_id_here
QB_CLIENT_SECRET=your_client_secret_here
QB_ACCESS_TOKEN=your_access_token_here
QB_REFRESH_TOKEN=your_refresh_token_here
QB_REALM_ID=your_realm_id_here
QB_ENVIRONMENT=sandbox
PROXY_PORT=8000
PROXY_BEARER_TOKEN=your_proxy_bearer_token_here
```

5. Generate a secure bearer token (optional but recommended):
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copy the generated token to `PROXY_BEARER_TOKEN` in your `.env` file.

## Usage

### Starting the Server

Run the FastAPI application:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000` (or the port specified in your `.env` file).

**Note**: 
- The proxy uses the hardcoded credentials from your `.env` file. All requests will be made using your configured QuickBooks account.
- If `PROXY_BEARER_TOKEN` is set in your `.env` file, all API requests (except `/health`) require a Bearer token in the `Authorization` header.
- The `/health` endpoint does not require authentication.

### API Endpoints

#### Health Check
```
GET /health
```
Returns the health status of the proxy.

#### Proxy Endpoints
```
GET|POST|PUT|PATCH|DELETE /v3/company/{realm_id}/customers/*
```
All Customers entity endpoints are proxied to QuickBooks API. The proxy maintains the exact same API schema.

**Note**: 
- All other entity endpoints (e.g., `/v3/company/{realm_id}/items/*`, `/v3/company/{realm_id}/invoices/*`) will return `403 Forbidden`.
- The `realm_id` in the URL path will be automatically replaced with your configured `QB_REALM_ID` from the `.env` file.

## Examples

### List Customers

```bash
# Note: The realm_id in the URL will be replaced with your configured QB_REALM_ID
# If PROXY_BEARER_TOKEN is set, include it in the Authorization header
curl -X GET "https://quickbooks.wardsrental.com/v3/company/any_realm_id/query?query=SELECT * FROM Customer" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here"
```

### Get Specific Customer

```bash
curl -X GET "https://quickbooks.wardsrental.com/v3/company/any_realm_id/customers/1" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here"
```

### Create Customer

```bash
curl -X POST "https://quickbooks.wardsrental.com/v3/company/any_realm_id/customers" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here" \
  -d '{
    "DisplayName": "Test Customer",
    "CompanyName": "Test Company"
  }'
```

### Update Customer

```bash
curl -X POST "https://quickbooks.wardsrental.com/v3/company/any_realm_id/customers" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here" \
  -d '{
    "Id": "1",
    "SyncToken": "0",
    "DisplayName": "Updated Customer Name"
  }'
```

### Query Customers

```bash
curl -X GET "https://quickbooks.wardsrental.com/v3/company/any_realm_id/query?query=SELECT * FROM Customer WHERE Active = true" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here"
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `QB_CLIENT_ID` | QuickBooks OAuth2 Client ID | Yes | - |
| `QB_CLIENT_SECRET` | QuickBooks OAuth2 Client Secret | Yes | - |
| `QB_ACCESS_TOKEN` | QuickBooks access token | Yes | - |
| `QB_REFRESH_TOKEN` | QuickBooks refresh token | Yes | - |
| `QB_REALM_ID` | QuickBooks Company ID / Realm ID | Yes | - |
| `QB_ENVIRONMENT` | Environment: `sandbox` or `production` | No | `sandbox` |
| `QB_TOKEN_URL` | OAuth2 token URL (for refresh) | No | `https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer` |
| `PROXY_PORT` | Port for the proxy server | No | `8000` |
| `PROXY_BEARER_TOKEN` | Bearer token for proxy API authentication | No | Empty (no auth required) |

## Security Considerations

- **Token Storage**: Tokens are stored in environment variables and loaded into memory. Keep your `.env` file secure and never commit it to version control.
- **HTTPS**: Always use HTTPS in production.
- **CORS**: The default CORS configuration allows all origins. Configure `allow_origins` in `main.py` for production.
- **Token Refresh**: The proxy automatically refreshes tokens when they expire. Ensure your `QB_REFRESH_TOKEN` is valid and not expired.

## Troubleshooting

### 401 Unauthorized
- Verify your `QB_ACCESS_TOKEN` and `QB_REFRESH_TOKEN` are correct in your `.env` file
- Check that your tokens haven't expired (they should refresh automatically)
- Verify your `QB_CLIENT_ID` and `QB_CLIENT_SECRET` are correct
- If tokens are expired, get new tokens from the [Intuit OAuth Playground](https://developer.intuit.com/app/developer/playground)

### 403 Forbidden
- The requested endpoint is not a Customers entity endpoint
- Only `/v3/company/{realm_id}/customers/*` paths are allowed

### Token Refresh Failures
- Verify your `QB_REFRESH_TOKEN` is still valid and not expired
- Get new tokens from the [Intuit OAuth Playground](https://developer.intuit.com/app/developer/playground) and update your `.env` file

## Docker Commands

### Build the Docker image
```bash
docker build -t quickbooks-proxy .
```

### Run the container
```bash
docker run -d \
  --name quickbooks-proxy \
  -p 8000:8000 \
  --env-file .env \
  quickbooks-proxy
```

### View logs
```bash
docker logs -f quickbooks-proxy
```

### Stop the container
```bash
docker stop quickbooks-proxy
```

### Remove the container
```bash
docker rm quickbooks-proxy
```

### Using Docker Compose
```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Project Structure

```
quickbooks-proxy/
├── main.py              # FastAPI application and routes
├── auth.py              # OAuth2 authentication handlers
├── proxy.py             # Request filtering and forwarding logic
├── config.py            # Configuration management
├── pyproject.toml       # Project dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── .dockerignore        # Docker ignore file
├── .env.example         # Environment variables template
└── README.md            # This file
```

## License

[Add your license here]

## Support

For issues related to:
- **QuickBooks API**: See [Intuit Developer Documentation](https://developer.intuit.com/app/developer/qbo/docs)
- **This Proxy**: Open an issue in the repository

