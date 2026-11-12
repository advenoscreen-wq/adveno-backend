# Adveno API

## Conventions

- Base path: `/api/v1`
- Content type: `application/json`
- Timestamps: UTC ISO 8601
- Authentication: protected endpoints will use backend-validated credentials
- Errors: `{ "error": { "code": "...", "message": "...", "status_code": 400 } }`
- Secrets, tokens, credentials, and internal exception details are never
  returned in API responses.

Business endpoints will be documented here when approved and implemented.

## Health endpoints

### `GET /api/v1/health`

Reports that the API process is running. No authentication is required.

**Response `200`:**

```json
{"status": "ok"}
```

### `GET /api/v1/ready`

Checks critical dependency readiness. No authentication is required.

**Response `200`:**

```json
{"status": "ready"}
```

**Response `503`:** The database is unavailable.

```json
{"detail": "Database is unavailable"}
```
