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

## Media uploads

### `POST /api/v1/media/upload-url`

Requests a Supabase Storage signed upload URL. Requires a valid Supabase access
token in `Authorization: Bearer <access_token>`. The backend creates a unique
object path scoped to the authenticated user and requests a signed URL using
the caller's token, so Supabase Storage policies still apply.

**Request:**

```json
{"file_name": "welcome.png"}
```

**Response `200`:**

```json
{
  "signed_url": "https://<project>.supabase.co/storage/v1/object/upload/sign/...",
  "storage_path": "users/<user-id>/<unique-id>/welcome.png"
}
```

Upload the file directly to `signed_url` with an HTTP `PUT`. Retain
`storage_path` for creating the media metadata record in a later request. This
endpoint only creates the upload URL; it does not create a media record.

### `POST /api/v1/media`

Registers metadata after the file has been uploaded. Requires a valid Supabase
access token in `Authorization: Bearer <access_token>`. The storage path must
belong to the authenticated user. A bucket-prefixed path such as
`adveno/users/<user-id>/<unique-id>/file.png` is accepted when `adveno` is the
configured bucket; the bucket name is removed before the object path is stored.

**Request:**

```json
{
  "name": "Lobby banner",
  "media_type": "IMAGE",
  "mime_type": "image/png",
  "storage_path": "users/<user-id>/<unique-id>/file.png",
  "file_size": 2048,
  "width": 1920,
  "height": 1080,
  "duration_seconds": null
}
```

`media_type` is `IMAGE` or `VIDEO`. `width`, `height`, and `duration_seconds`
are optional. The backend generates a unique `checksum` value and returns it
with the created media record. A newly generated checksum lets clients detect
that a replacement has been saved and refresh the media.
Registering an already registered storage path returns `409 MEDIA_ALREADY_REGISTERED`;
a path outside the authenticated user's storage folder returns `422`.
Create, get, and update responses include `media_url`, a public Supabase Storage
URL built from the configured project URL, bucket, and object path. The bucket
must be configured as public for the URL to be readable without authentication.

### `GET /api/v1/media/{media_id}`

Returns a media asset owned by the authenticated user, with its public
`media_url`. Unknown or another user's media returns `404 MEDIA_NOT_FOUND`.

### `GET /api/v1/media`

Lists media owned by the authenticated user. Supports `filter_by_name` for a
case-insensitive partial name match, `page` (default `1`), and `limit` (default
`20`, maximum `100`). Each item includes its public `media_url`.

```json
{
  "items": [],
  "total_pages": 0,
  "total_items": 0,
  "has_next": false,
  "has_prev": false,
  "limit": 20,
  "page": 1
}
```

### `POST /api/v1/media/{media_id}/upload-url`

Requests an upload URL to replace the object for an existing active media record.
Requires a valid Supabase access token. The media record must belong to the
authenticated user. The response contains the same `storage_path` and a signed
URL configured to allow overwriting that object. Upload the replacement file
directly to the URL; use `PUT` and retain the existing object path.

An unknown, deleted, or another user's media ID returns `404 MEDIA_NOT_FOUND`.

### `PUT /api/v1/media/{media_id}`

Updates an existing media record. Requires authentication. `is_replaced` is
required. `name` is always updated. When `false`, provide only `name`; file
metadata and checksum stay unchanged. When `true`, also provide the replacement file
metadata (`media_type`, `mime_type`, `storage_path`, and `file_size`; dimensions
and duration are optional). The backend generates a new unique checksum. Screens
assigned to playlists containing this media have their desired synchronization
revision incremented in the same transaction as the media update.

Rename request:


```json
{"is_replaced": false, "name": "Lobby banner"}
```

Replacement request:

```json
{
  "is_replaced": true,
  "name": "Updated banner",
  "media_type": "IMAGE",
  "mime_type": "image/png",
  "storage_path": "users/<user-id>/<unique-id>/file.png",
  "file_size": 2048,
  "width": 1920,
  "height": 1080
}
```

The response contains the saved media metadata and `screen_sync`, an array of
`screen_id` and `desired_revision` values for every active screen using the
media through an assigned playlist. If no screen currently uses the media, the
array is empty.

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

## Playlists

### `POST /api/v1/playlists`

Creates a playlist for the authenticated user with selected media assets. Every
media ID must exist and belong to that user. Item positions must be unique;
items are returned in position order. `duration_seconds` is optional per item.

**Request:**

```json
{
  "name": "Lobby playlist",
  "description": "Lobby content",
  "items": [
    {"media_asset_id": "uuid", "position": 1, "duration_seconds": 15},
    {"media_asset_id": "uuid", "position": 2}
  ]
}
```

An unavailable or unowned media ID returns `404 MEDIA_NOT_FOUND`.

### `GET /api/v1/playlists`

Lists the authenticated user's playlists using the shared pagination response.
Supports `page` (default `1`), `limit` (default `20`, maximum `100`), and
`filter_by_title`, which searches both playlist names and descriptions.

### `GET /api/v1/playlists/{playlist_id}`

Returns a playlist and its items for the authenticated owner. Missing playlists
and playlists owned by another user return `404 PLAYLIST_NOT_FOUND`.

### `PUT /api/v1/playlists/{playlist_id}`

Replaces the playlist name, description, and complete ordered item list. The
item list may be empty. Every selected media ID must exist and belong to the
authenticated user. Active screens assigned to the playlist have their desired
sync revision incremented after the update.

### `DELETE /api/v1/playlists/{playlist_id}`

Deletes the authenticated user's playlist, its items, and all active and
historical screen assignments. Screens currently assigned to it have their
desired sync revision incremented so they can clear the deleted playlist.
Returns `204 NO CONTENT`; an unknown or unowned playlist returns
`404 PLAYLIST_NOT_FOUND`.

### `PATCH /api/v1/screens/{screen_id}`

Updates a screen's user-managed display name. Requires a valid Supabase access
token. The screen must belong to the authenticated user. Device details such as
`device_model`, `app_version`, heartbeat, screen code, and synchronization state
remain managed by the TV/backend.

**Request:** `{"name": "Lobby TV"}`

**Response `200`:** the updated screen ID, screen code, name, status, and update
timestamp. An unknown or another user's screen returns `404 SCREEN_NOT_FOUND`.

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
