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

### `GET /api/v1/auth/google/request`

Creates a single-use OAuth state in the cache and redirects the browser to
the configured Google OAuth authorization URL using PKCE. The state and code
verifier are held server-side, and the browser receives a matching short-lived
HttpOnly state cookie.

### Starting OAuth login

Starts the configured Supabase OAuth flow. The backend generates and stores a
single-use CSRF state, then redirects the browser to the provider.

### `GET /api/v1/auth/google/callback`

Validates and consumes the single-use OAuth state, exchanges the authorization
code with its PKCE verifier, sets the Supabase refresh token in the configured
HttpOnly cookie, and redirects to `FRONTEND_AFTER_LOGIN_URL`. Provider authorization errors return
the standard JSON error envelope; disabled signups return `403 SIGNUP_DISABLED`.

### `POST /api/v1/auth/refresh`

Accepts a Supabase refresh token in the JSON request body and returns the new
access token and rotated refresh token.

**Request:**

```json
{"refresh_token": "..."}
```

**Response `200`:**

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

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
