# QuickBooks Proxy API - Testing Guide

This guide provides examples for testing the QuickBooks Proxy API endpoints. The proxy only allows Customers entity endpoints and uses your configured QuickBooks account credentials.

## Prerequisites

1. Ensure the proxy server is running:
   ```bash
   python main.py
   ```
   Or:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. Verify your `.env` file is configured with valid QuickBooks credentials:
   - `QB_ACCESS_TOKEN`
   - `QB_REFRESH_TOKEN`
   - `QB_REALM_ID`
   - `QB_CLIENT_ID`
   - `QB_CLIENT_SECRET`
   - `PROXY_BEARER_TOKEN` (optional, but recommended for production)

3. The server should be accessible at `http://localhost:8000` (or your configured port)

## Authentication

If `PROXY_BEARER_TOKEN` is set in your `.env` file, all API requests (except `/health`) require authentication using a Bearer token in the `Authorization` header:

```bash
Authorization: Bearer your_proxy_bearer_token_here
```

**Note**: The `/health` endpoint does not require authentication.

## Base URL

```
http://localhost:8000
```

**Note**: The `realm_id` in the URL path will be automatically replaced with your configured `QB_REALM_ID` from the `.env` file. You can use any realm_id in the URL, and it will be normalized to your configured one.

---

## 1. Health Check

Test if the proxy server is running and healthy.

### Request
```bash
curl -X GET "http://localhost:8000/health" \
  -H "Accept: application/json"
```

### Expected Response
```json
{
  "status": "healthy",
  "realm_id": "1234567890"
}
```

---

## 2. List All Customers

Retrieve a list of all customers from your QuickBooks account.

### Request
```bash
curl -X GET "http://localhost:8000/v3/company/any_realm_id/customers" \
  -H "Accept: application/json"
```

### Expected Response
```json
{
  "QueryResponse": {
    "Customer": [
      {
        "Id": "1",
        "DisplayName": "Customer Name",
        "CompanyName": "Company Name",
        "Active": true,
        ...
      }
    ],
    "maxResults": 1
  },
  "time": "2024-01-01T00:00:00.000-08:00"
}
```

---

## 3. Get Specific Customer by ID

Retrieve details of a specific customer by their ID.

### Request
```bash
curl -X GET "http://localhost:8000/v3/company/any_realm_id/customers/1" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here"
```

### Expected Response
```json
{
  "Customer": {
    "Id": "1",
    "SyncToken": "0",
    "DisplayName": "Customer Name",
    "CompanyName": "Company Name",
    "Active": true,
    "Balance": 0.0,
    ...
  },
  "time": "2024-01-01T00:00:00.000-08:00"
}
```

---

## 4. Create a New Customer

Create a new customer in your QuickBooks account.

### Request
```bash
curl -X POST "http://localhost:8000/v3/company/any_realm_id/customers" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here" \
  -d '{
    "DisplayName": "Test Customer",
    "CompanyName": "Test Company Inc",
    "GivenName": "John",
    "FamilyName": "Doe",
    "PrimaryPhone": {
      "FreeFormNumber": "555-1234"
    },
    "PrimaryEmailAddr": {
      "Address": "john.doe@testcompany.com"
    }
  }'
```

### Expected Response
```json
{
  "Customer": {
    "Id": "2",
    "SyncToken": "0",
    "DisplayName": "Test Customer",
    "CompanyName": "Test Company Inc",
    ...
  },
  "time": "2024-01-01T00:00:00.000-08:00"
}
```

---

## 5. Update an Existing Customer

Update an existing customer. You must include the `Id` and `SyncToken` from the current customer record.

### Request
```bash
curl -X POST "http://localhost:8000/v3/company/any_realm_id/customers" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here" \
  -d '{
    "Id": "1",
    "SyncToken": "0",
    "DisplayName": "Updated Customer Name",
    "CompanyName": "Updated Company Name"
  }'
```

### Expected Response
```json
{
  "Customer": {
    "Id": "1",
    "SyncToken": "1",
    "DisplayName": "Updated Customer Name",
    "CompanyName": "Updated Company Name",
    ...
  },
  "time": "2024-01-01T00:00:00.000-08:00"
}
```

**Note**: The `SyncToken` increments with each update. Always use the latest `SyncToken` from the customer record.

---

## 6. Query Customers

Query customers using QuickBooks SQL-like query syntax.

### Request - Get Active Customers
```bash
curl -X GET "http://localhost:8000/v3/company/any_realm_id/query?query=SELECT * FROM Customer WHERE Active = true" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here"
```

### Request - Get Customers by Name
```bash
curl -X GET "http://localhost:8000/v3/company/any_realm_id/query?query=SELECT * FROM Customer WHERE DisplayName LIKE '%Test%'" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here"
```

### Request - Get Customers with Balance
```bash
curl -X GET "http://localhost:8000/v3/company/any_realm_id/query?query=SELECT * FROM Customer WHERE Balance > 0" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here"
```

### Expected Response
```json
{
  "QueryResponse": {
    "Customer": [...],
    "maxResults": 20
  },
  "time": "2024-01-01T00:00:00.000-08:00"
}
```

---

## 7. Delete a Customer (Sparse Update)

Mark a customer as inactive (QuickBooks doesn't allow hard deletes).

### Request
```bash
curl -X POST "http://localhost:8000/v3/company/any_realm_id/customers" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here" \
  -d '{
    "Id": "1",
    "SyncToken": "1",
    "Active": false,
    "sparse": true
  }'
```

### Expected Response
```json
{
  "Customer": {
    "Id": "1",
    "SyncToken": "2",
    "Active": false,
    ...
  },
  "time": "2024-01-01T00:00:00.000-08:00"
}
```

---

## 8. Get Customer with Additional Fields

Retrieve a customer with additional fields like addresses and contact info.

### Request
```bash
curl -X GET "http://localhost:8000/v3/company/any_realm_id/customers/1?minorversion=65" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here"
```

---

## 9. Test Access Denied (Non-Customers Endpoint)

Test that non-Customers endpoints are properly blocked.

### Request
```bash
curl -X GET "http://localhost:8000/v3/company/any_realm_id/items" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your_proxy_bearer_token_here"
```

### Expected Response
```json
{
  "error": "Access denied. Only Customers entity endpoints are allowed."
}
```

**Status Code**: `403 Forbidden`

---

## 10. Test Invalid Authentication

If tokens are invalid or expired, you should receive an authentication error.

### Request
```bash
curl -X GET "http://localhost:8000/v3/company/any_realm_id/customers" \
  -H "Accept: application/json"
```

### Expected Response (if tokens are invalid)
```json
{
  "error": "Not authenticated. Please check your QB_ACCESS_TOKEN and QB_REFRESH_TOKEN in .env file."
}
```

**Status Code**: `401 Unauthorized`

---

## Testing with Different Tools

### Using HTTPie

```bash
# List customers
http GET http://localhost:8000/v3/company/any_realm_id/customers Accept:application/json

# Create customer
http POST http://localhost:8000/v3/company/any_realm_id/customers \
  Content-Type:application/json \
  Accept:application/json \
  DisplayName="Test Customer" \
  CompanyName="Test Company"
```

### Using Postman

1. Create a new request
2. Set method to `GET`, `POST`, etc.
3. Enter URL: `http://localhost:8000/v3/company/any_realm_id/customers`
4. Add headers:
   - `Accept: application/json`
   - `Content-Type: application/json` (for POST/PUT requests)
5. For POST requests, add JSON body in the "Body" tab

### Using Python requests

```python
import requests

base_url = "http://localhost:8000"

# List customers
response = requests.get(
    f"{base_url}/v3/company/any_realm_id/customers",
    headers={"Accept": "application/json"}
)
print(response.json())

# Create customer
customer_data = {
    "DisplayName": "Test Customer",
    "CompanyName": "Test Company Inc"
}
response = requests.post(
    f"{base_url}/v3/company/any_realm_id/customers",
    json=customer_data,
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
)
print(response.json())
```

### Using JavaScript (fetch)

```javascript
const baseUrl = 'http://localhost:8000';

// List customers
fetch(`${baseUrl}/v3/company/any_realm_id/customers`, {
  method: 'GET',
  headers: {
    'Accept': 'application/json'
  }
})
  .then(response => response.json())
  .then(data => console.log(data));

// Create customer
fetch(`${baseUrl}/v3/company/any_realm_id/customers`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  body: JSON.stringify({
    DisplayName: 'Test Customer',
    CompanyName: 'Test Company Inc'
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## Common Response Codes

| Status Code | Description |
|-------------|-------------|
| `200 OK` | Request successful |
| `201 Created` | Resource created successfully |
| `400 Bad Request` | Invalid request format or parameters |
| `401 Unauthorized` | Authentication failed or tokens invalid |
| `403 Forbidden` | Access denied (non-Customers endpoint) |
| `404 Not Found` | Resource not found |
| `500 Internal Server Error` | Server error |
| `502 Bad Gateway` | Error forwarding request to QuickBooks |
| `504 Gateway Timeout` | Request to QuickBooks timed out |

---

## Troubleshooting

### Issue: 401 Unauthorized
- **Solution**: Check your `.env` file and ensure `QB_ACCESS_TOKEN` and `QB_REFRESH_TOKEN` are valid
- Get new tokens from [Intuit OAuth Playground](https://developer.intuit.com/app/developer/playground)

### Issue: 403 Forbidden
- **Solution**: You're trying to access a non-Customers endpoint. Only `/v3/company/{realm_id}/customers/*` paths are allowed

### Issue: 400 Bad Request
- **Solution**: Check your request body format. Ensure it's valid JSON and includes required fields

### Issue: Connection Refused
- **Solution**: Ensure the proxy server is running on the correct port

### Issue: Invalid SyncToken
- **Solution**: Always fetch the latest customer record first to get the current `SyncToken` before updating

---

## Quick Test Script

Save this as `test_api.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
REALM_ID="any_realm_id"

echo "1. Health Check"
curl -s -X GET "${BASE_URL}/health" | jq .

echo -e "\n2. List Customers"
curl -s -X GET "${BASE_URL}/v3/company/${REALM_ID}/customers" \
  -H "Accept: application/json" | jq .

echo -e "\n3. Test Access Denied (Items endpoint)"
curl -s -X GET "${BASE_URL}/v3/company/${REALM_ID}/items" \
  -H "Accept: application/json" | jq .
```

Make it executable and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Notes

1. **Realm ID**: The realm_id in the URL is automatically replaced with your configured `QB_REALM_ID`. You can use any value.

2. **Token Refresh**: The proxy automatically refreshes tokens when they expire. No action needed.

3. **Rate Limiting**: QuickBooks API has rate limits. If you receive rate limit errors, wait before retrying.

4. **Sandbox vs Production**: Ensure your `QB_ENVIRONMENT` matches the environment where you obtained your tokens.

5. **SyncToken**: Always use the latest `SyncToken` when updating customers to avoid conflicts.

