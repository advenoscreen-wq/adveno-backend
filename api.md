# Adveno API

## Conventions

- Base path: `/api/v1`
- Content type: `application/json`
- Timestamps: UTC ISO 8601
- Authentication: protected endpoints will use backend-validated credentials
- Errors: `{ "error": { "code": "...", "message": "...", "status_code": 400 } }`
- Secrets, credentials, and internal exception details are never returned
  in API responses. Pairing tokens are returned once by the pairing request
  endpoint so the TV can complete pairing.

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

## Screen pairing

### `POST /api/v1/pairing/sessions`

Creates a pending pairing session for a TV. The backend stores only a SHA-256
hash of the generated token and returns the raw token once. No screen record is
created by this request. The frontend must select a pairing type. For
both pairing types, the new session initially has no `screen_id`. A reconnect
target can be selected later.

**Request:**

```json
{"pairing_type": "NEW_SCREEN"}
```

```json
{"pairing_type": "RECONNECT_EXISTING"}
```

**Response `201`:**

```json
{
  "session_id": "uuid",
  "pairing_token": "one-time-token",
  "expires_at": "2026-11-13T15:10:00Z"
}
```

### `GET /api/v1/pairing/sessions/{session_id}`

Returns the pairing status for the specified session. Send the pairing token
received from the create endpoint in the `X-Pairing-Token` header.

**Response `200`:**

```json
{"status": "PENDING"}
```

An unknown session ID or invalid token returns `404 PAIRING_SESSION_NOT_FOUND`.
The session status is `PENDING` after creation, `CONNECTING` after approval,
and `PAIRED` after screen creation or successful credential issuance. An
expired pending or connecting session is reported as `EXPIRED`.

### `GET /api/v1/pairing/sessions/verify`

Checks a scanned pairing session for an authenticated application user. Send a
valid Supabase access token in the `Authorization: Bearer <access_token>`
header and the scanned raw pairing token in the `X-Pairing-Token` header. The
server hashes the token to find the session. The response includes the session
status, expiry, selected pairing type, screen reference, and whether a screen
record currently exists. Expired sessions return `200` with `status: "EXPIRED"`; an unknown session returns
`404 PAIRING_SESSION_NOT_FOUND`. Missing or invalid authentication, or an
inactive/missing application user, returns `401 AUTHENTICATION_REQUIRED`.

**Response `200`:**

```json
{
  "session_id": "uuid",
  "status": "PENDING",
  "pairing_type": null,
  "screen_id": null,
  "screen_exists": false,
  "expires_at": "2026-11-13T15:10:00Z",
  "created_at": "2026-11-13T15:00:00Z"
}
```

### `POST /api/v1/pairing/sessions/approve`

Starts pairing for a pending session. Requires a valid Supabase access token in the
`Authorization` header and the scanned QR token in `X-Pairing-Token`. For
`NEW_SCREEN`, send an empty JSON object. For `RECONNECT_EXISTING`, send the ID
of an active screen owned by the authenticated user:

```json
{"screen_id": "uuid"}
```

Approval changes the session to `CONNECTING`. Reconnect associates the session
with the existing screen, preserves its data, and revokes its active credential.
The TV completes pairing by creating a new screen (`NEW_SCREEN`) or requesting
a credential (`RECONNECT_EXISTING`). Those operations set `PAIRED` and `paired_at`.
Expired sessions return `410 PAIRING_SESSION_EXPIRED`; sessions that are no
longer pending return `409 PAIRING_SESSION_NOT_PENDING`.

**Response `200`:**

```json
{
  "session_id": "uuid",
  "pairing_type": "NEW_SCREEN",
  "status": "CONNECTING",
  "screen_id": null,
  "paired_at": null
}
```

### `POST /api/v1/pairing/sessions/{session_id}/screen`

Creates a screen for a `CONNECTING` `NEW_SCREEN` session. Requires an authenticated
user and the session's raw token in `X-Pairing-Token`. The request is rejected
unless the session is `CONNECTING`; reconnect sessions and sessions that already
have a screen cannot create another one. The backend assigns the screen ID and
screen code, creates its credential, and changes the session to `PAIRED` with
`paired_at` in the same transaction.

```json
{
  "name": "Lobby TV",
  "device_model": "Model X",
  "app_version": "1.2.3"
}
```

The device fields are optional. The response contains `screen_id`,
`screen_code`, `name`, and a newly generated raw `credential`. The raw credential
is returned once; PostgreSQL stores only its SHA-256 hash. The TV should retain
the credential and use it for subsequent device authentication.

### `POST /api/v1/pairing/sessions/{session_id}/credential`

Issues a fresh credential for a `CONNECTING` reconnect session. Requires the session's raw
pairing token in `X-Pairing-Token`. The current active credential is revoked and
kept for history when present; a new credential is created if none exists. The
credential is returned once, with only its SHA-256 hash stored in PostgreSQL.
This changes the session to `PAIRED` and sets `paired_at`. Calling this endpoint
again for a completed session rotates the credential again.

**Response `200`:** `screen_id` and the new raw `credential`.

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
