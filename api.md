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

## BFF OAuth authentication

### `GET /api/v1/auth/oauth/login`

Starts the configured Supabase OAuth flow. The backend generates and stores a
single-use CSRF state, then redirects the browser to the provider.

### `GET /api/v1/auth/oauth/callback`

Validates and consumes the OAuth state, exchanges the authorization code, and
creates or loads the application user using the provider's verified identity.
The backend sets an HttpOnly application-session cookie and redirects to the
configured frontend URL. Provider access and refresh tokens are never returned
to the browser or stored in the application session cookie.

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
