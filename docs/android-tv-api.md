# Adveno Android TV API reference

This document is extracted from the current backend source. It describes the
routes registered under `/api/v1`, their schemas, use-case behavior, and the
limits of the current implementation. The backend code is the source of truth;
this document does not propose or imply unimplemented endpoints.

FastAPI's default interactive documentation is available at `/docs`; the
generated OpenAPI document is at `/openapi.json`.

## Android TV integration summary

The Android TV client uses these device-facing operations:

| Purpose | Method and path | Credential |
| --- | --- | --- |
| Start pairing | `POST /api/v1/pairing/sessions` | None |
| Poll pairing status | `GET /api/v1/pairing/sessions/{session_id}` | `X-Pairing-Token` |
| Register a new screen | `POST /api/v1/pairing/sessions/{session_id}/screen` | `X-Pairing-Token` only |
| Issue/rotate reconnect credential | `POST /api/v1/pairing/sessions/{session_id}/credential` | `X-Pairing-Token` |
| Check whether a sync is needed / heartbeat | `POST /api/v1/screens/sync-check` | Screen credential as Bearer token |
| Verify a stored screen credential on app startup | `POST /api/v1/screens/credential/verify` | Screen credential as Bearer token |
| Fetch assigned playlist and media metadata | `GET /api/v1/screens/assigned-playlist` | Screen credential as Bearer token |
| Acknowledge an applied sync revision | `POST /api/v1/screens/sync-acknowledgments` | Screen credential as Bearer token |
| Verify dashboard PIN and start a temporary settings session | `POST /api/v1/screens/admin-session/verify` | Screen credential as Bearer token |
| Revoke the TV's temporary settings session | `POST /api/v1/screens/admin-session/revoke` | Screen credential and `X-Admin-Session` |
| Log out this screen and revoke its credential | `POST /api/v1/screens/logout` | Screen credential and `X-Admin-Session` |

The dashboard-only endpoints `GET /pairing/sessions/verify` and
`POST /pairing/sessions/approve` require an app-user Supabase access token. They
are not authenticated by a screen credential.

New-screen registration is performed by the TV using its pairing token. The
management app's authenticated approval stores the screen owner on the pairing
session; the TV does not send or need a Supabase access token for registration.

## Authentication and headers

### App-user authentication

Management and approval routes use:

```http
Authorization: Bearer <supabase-access-token>
```

The backend verifies this JWT locally. It expects the configured Supabase
signing key (`kid`, EC P-256 `x` and `y` coordinates), algorithm `ES256`,
issuer `<SUPABASE_URL>/auth/v1`, audience `authenticated`, and the `exp`, `iat`,
and `sub` claims. The `sub` must be a UUID for an active application user. A
missing, invalid, expired, or unrecognized app-user token returns
`401 AUTHENTICATION_REQUIRED`.

### Screen-device authentication

After pairing, device routes use the raw screen credential returned once by the
screen creation or credential issuance response:

```http
Authorization: Bearer <screen-credential>
```

The server hashes the submitted credential with SHA-256 and looks up the hash.
PostgreSQL stores the hash, not the raw credential. Credentials have no
time-based expiration in the current domain model; disconnect/reconnect revokes
them. A valid request must also belong to an active screen.

Device-authentication outcomes:

| Condition | HTTP | Error code |
| --- | ---: | --- |
| Missing/malformed Bearer credential | 401 | `INVALID_SCREEN_CREDENTIAL` |
| No screen credential matches the supplied token | 404 | `SCREEN_NOT_FOUND` |
| Credential was revoked or screen is `INACTIVE` | 401 | `SCREEN_DISCONNECTED` |

### Protected TV settings session

The dashboard creates a PIN for a screen with
`POST /api/v1/screens/{screen_id}/admin-session`, authenticated by the app-user
Supabase access token. The response contains `session_id`, a six-digit `pin`,
and `expires_at`; the PIN is returned once and only its scrypt hash is stored.
PINs expire after five minutes. The dashboard must deliver the PIN to the TV
through its existing UX.

The TV verifies it with `POST /api/v1/screens/admin-session/verify`, sending
its screen credential as the Bearer token and `{"pin":"123456"}` in JSON.
Success returns `session_id`, a one-time `session_token`, and `expires_at`.
The TV stores that token securely and sends it in `X-Admin-Session` only for
the logout and admin-session revoke requests documented here. It is scoped to
the screen credential used during verification, expires after 15 minutes, and
expires after five minutes without a protected action. Incorrect PIN attempts
are limited to five per ten-minute window; excessive requests return
`429 ADMIN_PIN_RATE_LIMITED`. Invalid PIN returns `401 INVALID_ADMIN_PIN`.

Both protected requests use:

```http
Authorization: Bearer <screen-credential>
X-Admin-Session: <session-token>
```

Missing, expired, revoked, or other-screen session tokens return
`401 EXPIRED_SESSION`. A successful logout revokes both the screen credential
and its current admin session. Revoke the temporary session with
`POST /api/v1/screens/admin-session/revoke` (`204 No Content`) when leaving
settings without logging out. Normal sync checks, sync acknowledgments,
assigned-playlist requests, and playback reports continue to use only the
screen credential; they do not require or refresh this temporary session.

The TV should treat `SCREEN_NOT_FOUND` and `SCREEN_DISCONNECTED` as reasons to
clear its locally stored credential and return to pairing. A user-initiated
disconnect revokes the active credential; deleting a screen also removes
dependent credentials.

### Pairing token

Pairing status, approval, registration, and credential issuance use the raw
token returned by session creation in:

```http
X-Pairing-Token: <pairing-token>
```

Missing required headers normally produce FastAPI's `422` request-validation
response. A supplied but incorrect pairing token is deliberately reported as
`404 PAIRING_SESSION_NOT_FOUND`.

### Error response shapes

Application errors use this envelope:

```json
{
  "error": {
    "code": "PAIRING_SESSION_NOT_FOUND",
    "message": "Pairing session was not found.",
    "status_code": 404
  }
}
```

FastAPI schema and parameter validation errors use FastAPI's `detail` array
format, rather than the application-error envelope. The exact validation text
can vary with the invalid field.

## Enums used by TV and pairing flows

| Enum | Values | Meaning/use |
| --- | --- | --- |
| `PairingType` | `NEW_SCREEN`, `RECONNECT_EXISTING` | Required in session creation. For reconnect, the existing screen is selected later by the authenticated approver. |
| `PairingSessionStatus` | `PENDING`, `CONNECTING`, `PAIRED`, `EXPIRED` | Lifecycle returned by pairing status/verification/approval. |
| `ScreenStatus` | `ACTIVE`, `INACTIVE` | Management status. Device authentication rejects inactive screens. |
| `MediaType` | `IMAGE`, `VIDEO` | Media type in assigned playlist media metadata. |
| `MediaStatus` | `ACTIVE`, `DELETED` | Media lifecycle value included in assigned playlist media metadata. |
| `SyncStatus` | `PENDING`, `SYNCING`, `SYNCED`, `FAILED` | Internal sync-state enum. It is not returned by TV routes. |

`UserRole` (`ADMIN`, `USER`) is an app-user role, not a TV/device credential
type and is not included in the TV responses documented below.

## Domain entities

The following are the backend's domain entities, traced from
`src/domain/entities`. They describe internal business state; they are not all
serialized as API responses. API routes expose the response schemas documented
in each endpoint section, and in particular never expose stored credential
hashes.

| Entity | Fields (domain types) | Role and TV/API relevance |
| --- | --- | --- |
| `User` | `id: UUID`; `role: UserRole = USER`; `is_active: bool = true`; `created_at`, `updated_at: datetime` | Application account used as the screen owner and for management authorization. It is not a TV login credential. |
| `Screen` | `id: UUID`; `user_id: UUID`; `screen_code: str`; `name: str`; `device_model`, `app_version: str | None`; `status: ScreenStatus = ACTIVE`; `last_seen_at`, `last_successful_sync_at: datetime | None`; `created_at`, `updated_at: datetime` | Registered TV. The backend generates a readable `screen_code`. Device authentication requires an active screen. Heartbeat/sync-check updates `last_seen_at`. |
| `ScreenCredential` | `id: UUID`; `screen_id: UUID`; `credential_hash: str`; `created_at: datetime`; `last_used_at`, `revoked_at: datetime | None` | Device-auth record. Only the hash is persisted; the raw credential is returned by pairing creation/issuance responses. Revocation preserves credential history. |
| `ScreenPairingSession` | `id: UUID`; `token_hash: str`; `expires_at`, `created_at: datetime`; `pairing_type: PairingType | None`; `screen_id`, `approved_by_user_id: UUID | None`; `status: PairingSessionStatus = PENDING`; `paired_at: datetime | None` | Temporary pairing state. The raw pairing token is returned once; only its hash is stored. Approval records the owning app user in `approved_by_user_id`; the TV uses the pairing token and session ID for new-screen registration. Reconnect selects an existing screen at approval. |
| `ScreenSyncState` | `id: UUID`; `screen_id: UUID`; `desired_revision: int = 0`; `applied_revision: int = 0`; `sync_status: SyncStatus = PENDING`; `last_sync_started_at`, `last_successful_sync_at: datetime | None`; `last_error: str | None`; `updated_at: datetime` | Per-screen synchronization bookkeeping. `sync-check` exposes `need_sync` and `desired_revision`; the acknowledgment route updates the applied revision. |
| `ScreenPlaylistAssignment` | `id: UUID`; `screen_id`, `playlist_id: UUID`; `assigned_at: datetime`; `unassigned_at: datetime | None` | Assignment history. An assignment is active while `unassigned_at` is null. The TV playlist endpoint uses the active assignment. |
| `Playlist` | `id: UUID`; `user_id: UUID`; `name: str`; `description: str | None`; `version: int = 1`; `items: list[PlaylistItem]`; `created_at`, `updated_at: datetime` | Ordered media collection returned to a screen with its version and items. The TV response serializes media details and a public media URL. |
| `PlaylistItem` | `id: UUID`; `playlist_id`, `media_asset_id: UUID`; `position: int`; `duration_seconds: int | None`; `created_at: datetime` | One ordered media entry. Positions and any supplied duration must be positive. TV response includes item duration and nested media metadata. |
| `ScreenPlaybackEvent` | `event_id`, `screen_id`, `playlist_id`, `playlist_item_id`, `media_asset_id: UUID`; `playlist_version: int`; `media_checksum: str`; `played_at`, `received_at: datetime`; `played_complete_at: datetime | None` | Immutable screen-reported playback record. Identifier values remain available after associated playlist, item, media, or screen records are deleted. |
| `MediaAsset` | `id: UUID`; `user_id: UUID`; `name`, `mime_type`, `storage_path`, `checksum: str`; `media_type: MediaType`; `file_size: int`; `width`, `height`, `duration_seconds: int | None`; `status: MediaStatus = ACTIVE`; `created_at`, `updated_at: datetime` | Stored image/video metadata. Only active media is playlist-compatible. The TV playlist response adds `media_url`; the entity itself has no URL field. |
| `AuditLog` | `id: UUID`; `action: str`; `admin_id`, `screen_id: UUID | None`; `details: dict[str, Any]`; `created_at: datetime` | Immutable audit event; not part of the current TV response contract. |
| `AdminProfile` | Alias of `User`; same fields as `User` | Backward-compatible alias, not a separate persisted/domain shape. |

Domain validation also enforces timezone-aware timestamps, nonblank required
names/paths/checksums, positive playlist positions and durations, valid pairing
state transitions, and `0 <= applied_revision <= desired_revision`. These
invariants are useful when interpreting responses but do not add fields to the
wire format.

## Pairing endpoints

### 1. Create a pairing session

**Method/path:** `POST /api/v1/pairing/sessions`
**Authentication:** None
**Status:** `201 Created`

Request schema: `CreateScreenPairingSessionRequest`. Extra fields are forbidden.

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `pairing_type` | `PairingType` string | Yes | `NEW_SCREEN` or `RECONNECT_EXISTING` |

Example request:

```json
{"pairing_type":"NEW_SCREEN"}
```

Example response (`CreateScreenPairingSessionResponse`):

```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "pairing_token": "generated-one-time-token",
  "expires_at": "2026-11-19T10:10:00Z"
}
```

Response fields: `session_id` is a UUID; `pairing_token` is a raw random string;
`expires_at` is a timestamp. The backend creates a 32-byte URL-safe random
token, persists only its SHA-256 hash, creates a `PENDING` session, and sets
expiry to ten minutes after creation. It does not create a screen. Both pairing
types initially have `screen_id = null`.

Errors: `422` for a missing/invalid `pairing_type` or extra request fields.

### 2. Poll pairing-session status

**Method/path:** `GET /api/v1/pairing/sessions/{session_id}`
**Authentication:** Pairing token only; no app-user JWT
**Path:** `session_id` — UUID
**Required header:** `X-Pairing-Token`
**Status:** `200 OK`

No query parameters or body.

Request example:

```http
GET /api/v1/pairing/sessions/3fa85f64-5717-4562-b3fc-2c963f66afa6
X-Pairing-Token: generated-one-time-token
```

Response schema: `ScreenPairingSessionStatusResponse`.

```json
{"status":"PENDING"}
```

The response contains only `status`. If a stored `PENDING` or `CONNECTING`
session has passed `expires_at`, this read reports `EXPIRED` with HTTP 200; the
read does not itself persist the expiration transition. A wrong token or
unknown session returns `404 PAIRING_SESSION_NOT_FOUND`. A missing pairing
header or invalid UUID path parameter returns `422`.

### 3. Verify a scanned session (dashboard/app-user endpoint)

**Method/path:** `GET /api/v1/pairing/sessions/verify`
**Authentication:** App-user Supabase Bearer token and pairing token
**Required headers:** `Authorization`, `X-Pairing-Token`
**Status:** `200 OK`

No path parameters, query parameters, or request body.

Response schema: `VerifyScreenPairingSessionResponse`.

```json
{
  "session_id":"3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status":"PENDING",
  "pairing_type":"NEW_SCREEN",
  "screen_id":null,
  "screen_exists":false,
  "expires_at":"2026-11-19T10:10:00Z",
  "created_at":"2026-11-19T10:00:00Z"
}
```

| Field | Type | Nullable |
| --- | --- | --- |
| `session_id` | UUID | No |
| `status` | `PairingSessionStatus` | No |
| `pairing_type` | `PairingType` | Yes |
| `screen_id` | UUID | Yes |
| `screen_exists` | Boolean | No |
| `expires_at` | Timestamp | No |
| `created_at` | Timestamp | No |

`screen_exists` is computed as whether `screen_id` is non-null; it does not
perform a separate screen-record lookup. An expired pending/connecting session
is returned with `status: EXPIRED` and HTTP 200. Errors: `401
AUTHENTICATION_REQUIRED`, `404 PAIRING_SESSION_NOT_FOUND`, and `422` for a
missing `X-Pairing-Token`.

### 4. Approve a pairing session (dashboard/app-user endpoint)

**Method/path:** `POST /api/v1/pairing/sessions/approve`
**Authentication:** App-user Supabase Bearer token and pairing token
**Required headers:** `Authorization`, `X-Pairing-Token`
**Status:** `200 OK`

Request schema: `ApproveScreenPairingSessionRequest`. Extra fields are
forbidden.

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `screen_id` | UUID or null | No | Required for `RECONNECT_EXISTING`; must be omitted/null for `NEW_SCREEN`. |

For a new screen, send `{}`. For reconnect:

```json
{"screen_id":"3fa85f64-5717-4562-b3fc-2c963f66afa6"}
```

Response schema: `ApproveScreenPairingSessionResponse`.

```json
{
  "session_id":"3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "pairing_type":"RECONNECT_EXISTING",
  "status":"CONNECTING",
  "screen_id":"4fa85f64-5717-4562-b3fc-2c963f66afa6",
  "paired_at":null
}
```

On `NEW_SCREEN`, approval changes status to `CONNECTING`; it does not create a
screen and response `screen_id` and `paired_at` are null. On reconnect, the
selected screen must exist, belong to the authenticated user, and be active.
The session references that existing screen and its current active credential
is revoked (history is retained). Approval still returns `CONNECTING` and null
`paired_at`; the new credential issuance completes reconnect.

Errors: `401 AUTHENTICATION_REQUIRED`; `404 PAIRING_SESSION_NOT_FOUND` or
`SCREEN_NOT_FOUND`; `409 PAIRING_SESSION_NOT_PENDING` or `SCREEN_NOT_ELIGIBLE`;
`410 PAIRING_SESSION_EXPIRED`; `422 PAIRING_TYPE_REQUIRED`, `SCREEN_ID_REQUIRED`,
`SCREEN_ID_NOT_ALLOWED`, invalid body, or missing pairing header.

### 5. Register a new screen after approval

**Method/path:** `POST /api/v1/pairing/sessions/{session_id}/screen`
**Authentication:** Pairing token only; no app-user JWT
**Path:** `session_id` — UUID
**Required header:** `X-Pairing-Token`
**Status:** `201 Created`

Request schema: `CreatePairedScreenRequest`. Extra fields are forbidden.

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `name` | String | Yes | No explicit Pydantic length/blank constraint; domain rejects blank names. |
| `device_model` | String or null | No | Defaults to null. |
| `app_version` | String or null | No | Defaults to null. |

Example:

```json
{"name":"Lobby TV","device_model":"Model X","app_version":"1.2.3"}
```

Response schema: `CreatePairedScreenResponse`.

```json
{
  "screen_id":"4fa85f64-5717-4562-b3fc-2c963f66afa6",
  "screen_code":"SCR-ABCD-EFGH-JKLM-NPQR",
  "name":"Lobby TV",
  "credential":"raw-screen-credential-returned-once"
}
```

The screen owner is taken from the user who approved the pairing session, not
from a token or field supplied by the TV. The backend generates the screen UUID
and human-readable screen code,
creates an initial sync state (`desired_revision=1`, `applied_revision=0`),
creates one active credential, assigns the screen to the pairing session, and
sets session status to `PAIRED` with `paired_at`. Only the credential hash is
stored. The raw `credential` is returned once and must be stored securely by
the TV.

Errors: `404 PAIRING_SESSION_NOT_FOUND`;
`409 PAIRING_SESSION_NOT_PAIRED` or `PAIRING_SCREEN_ALREADY_CREATED`;
`409 PAIRING_OWNER_NOT_SET` for a session approved before its owner was recorded;
`410 PAIRING_SESSION_EXPIRED`; `422 NEW_SCREEN_PAIRING_REQUIRED`, body
validation, or missing pairing header.

### 6. Issue or rotate a screen credential (reconnect completion)

**Method/path:** `POST /api/v1/pairing/sessions/{session_id}/credential`
**Authentication:** Pairing token only; no app-user JWT
**Path:** `session_id` — UUID
**Required header:** `X-Pairing-Token`
**Status:** `200 OK`

No query parameters or request body.

Response schema: `IssuePairedScreenCredentialResponse`.

```json
{
  "screen_id":"4fa85f64-5717-4562-b3fc-2c963f66afa6",
  "credential":"new-raw-screen-credential-returned-once"
}
```

The session must reference a screen and be `CONNECTING` or `PAIRED`. Any
existing active credential for that screen is revoked before the new one is
created; credentials are retained for history and only one active credential
is allowed. Issuing a credential increments the screen's desired sync revision
so the newly connected TV fetches its assigned content. A `CONNECTING` session
becomes `PAIRED` with `paired_at`. Calling
the endpoint again on a `PAIRED` session is allowed and rotates the credential
again; clients should not retry blindly after receiving a successful response.

Errors: `404 PAIRING_SESSION_NOT_FOUND`; `409 PAIRING_SESSION_NOT_PAIRED`;
`410 PAIRING_SESSION_EXPIRED` for an expired pending/connecting session; `422`
for a missing pairing header or invalid UUID.

## Screen-device endpoints

### 7. Check whether synchronization is needed (also heartbeat)

**Method/path:** `POST /api/v1/screens/sync-check`
**Authentication:** Screen credential plus temporary settings session
**Required headers:** `Authorization: Bearer <screen-credential>` and
`X-Admin-Session: <session-token>`
**Path/query/body:** None
**Status:** `200 OK`

Response schema: `ScreenSyncCheckResponse`.

```json
{"need_sync":true,"desired_revision":4}
```

The response has two fields: `need_sync` (Boolean) and `desired_revision`
(non-negative integer). `need_sync` is true when the screen has no sync-state
row or when `desired_revision > applied_revision`; otherwise it is false. If
the state row is missing, this check creates one with desired revision `1` so
the screen performs a full sync. A newly created screen starts with revisions
`1/0`, so it receives `need_sync: true` until it acknowledges revision 1. When
`need_sync` is true, the backend marks the state `SYNCING` and records
`last_sync_started_at`; repeated checks during that sync do not reset its time.

Each successful call validates the credential, updates `screen.last_seen_at`
and `credential.last_used_at`, then reads sync state. Errors: `401
INVALID_SCREEN_CREDENTIAL`, `401 SCREEN_DISCONNECTED`, or `404 SCREEN_NOT_FOUND`.

### 8. Verify a stored screen credential

**Method/path:** `POST /api/v1/screens/credential/verify`
**Authentication:** Screen credential Bearer token
**Required header:** `Authorization: Bearer <screen-credential>`
**Path/query/body:** None
**Status:** `200 OK`

Response schema: `ScreenCredentialVerificationResponse`.

```json
{"valid":true}
```

Call this when the TV app starts and finds a locally stored credential. A
successful response means the credential belongs to an active screen and may
be used for TV requests. The request also updates `last_seen_at` and
`credential.last_used_at`. Unknown credentials return `404 SCREEN_NOT_FOUND`;
revoked credentials and inactive screens return `401 SCREEN_DISCONNECTED`.
Missing or malformed Bearer credentials return `401 INVALID_SCREEN_CREDENTIAL`.

### 9. Fetch assigned playlist and media metadata

**Method/path:** `GET /api/v1/screens/assigned-playlist`
**Authentication:** Screen credential Bearer token
**Required header:** `Authorization: Bearer <screen-credential>`
**Path/query/body:** None
**Status:** `200 OK`

Response schema: `AssignedScreenPlaylistResponse | null`. If no active playlist
assignment exists (or its playlist cannot be found for the screen owner), the
body is JSON `null`. Treat this `200` response as a valid empty state: do not
retry it as an API failure or show a synchronization error. The TV can display
its No Ads state and offer the normal Sync Now action.

Example response:

```json
{
  "id":"5fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name":"Lobby playlist",
  "description":"Welcome content",
  "version":3,
  "items":[
    {
      "id":"6fa85f64-5717-4562-b3fc-2c963f66afa6",
      "position":1,
      "duration_seconds":15,
      "media":{
        "id":"7fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name":"Welcome video",
        "media_type":"VIDEO",
        "mime_type":"video/mp4",
        "storage_path":"users/<user-id>/<object-id>/welcome.mp4",
        "file_size":2048000,
        "checksum":"unique-media-version-checksum",
        "width":1920,
        "height":1080,
        "duration_seconds":30,
        "status":"ACTIVE",
        "media_url":"https://<supabase-project>.supabase.co/storage/v1/object/public/<bucket>/users/<user-id>/<object-id>/welcome.mp4"
      }
    }
  ]
}
```

The response fields are:

| Object | Field | Type | Nullable |
| --- | --- | --- | --- |
| Playlist | `id` | UUID | No |
| Playlist | `name` | String | No |
| Playlist | `description` | String | Yes |
| Playlist | `version` | Integer | No |
| Playlist | `items` | Array, ordered by item `position` ascending | No |
| Item | `id` | UUID | No |
| Item | `position` | Integer | No |
| Item | `duration_seconds` | Integer | Yes |
| Item media | `id` | UUID | No |
| Item media | `name` | String | No |
| Item media | `media_type` | `IMAGE` or `VIDEO` | No |
| Item media | `mime_type` | String | No |
| Item media | `storage_path` | String | No |
| Item media | `file_size` | Integer | No |
| Item media | `checksum` | String | No |
| Item media | `width` | Integer | Yes |
| Item media | `height` | Integer | Yes |
| Item media | `duration_seconds` | Integer | Yes |
| Item media | `status` | `ACTIVE` or `DELETED` | No |
| Item media | `media_url` | String | No |

The endpoint also records `last_seen_at` and credential `last_used_at`. Errors:
`401 INVALID_SCREEN_CREDENTIAL`, `401 SCREEN_DISCONNECTED`, and `404
SCREEN_NOT_FOUND`.

### 10. Acknowledge an applied synchronization revision

**Method/path:** `POST /api/v1/screens/sync-acknowledgments`
**Authentication:** Screen credential Bearer token
**Required header:** `Authorization: Bearer <screen-credential>`
**Path/query:** None
**Request schema:** `ScreenSyncAcknowledgmentRequest`
**Success:** `202 Accepted`, empty response body

Request body:

```json
{"applied_revision":4}
```

| Field | Type | Required | Validation |
| --- | --- | --- | --- |
| `applied_revision` | Integer | Yes | Non-negative; identifies the desired revision successfully applied by the TV. |

The TV sends the `desired_revision` returned by its latest `sync-check`, and
only after applying the fetched playlist/configuration and making required
media available. The async handler persists the acknowledgment before
returning `202 Accepted`; it updates `applied_revision` and
`last_successful_sync_at`. It must not advance beyond `desired_revision`. A
future revision returns `409 Conflict`; duplicate acknowledgment of the
already applied revision is idempotent, and stale acknowledgments must not
move the applied revision backward. Afterward, the TV can call `sync-check` to
learn whether a newer revision needs synchronization.

Authentication failures use the screen-device errors: `401
INVALID_SCREEN_CREDENTIAL`, `401 SCREEN_DISCONNECTED`, or `404
SCREEN_NOT_FOUND`. Missing sync state returns `404 SCREEN_SYNC_STATE_NOT_FOUND`;
a negative or malformed revision returns `422`.

### 11. Report completed ad playback events

**Method/path:** `POST /api/v1/screens/playback-events`
**Authentication:** Screen credential Bearer token
**Required header:** `Authorization: Bearer <screen-credential>`
**Request schema:** `ReportScreenPlaybackEventsRequest`
**Success:** `202 Accepted`

Request body:

```json
{
  "events": [
    {
      "event_id": "f6b9d59d-9062-45f3-96cc-a899278c12e4",
      "playlist_id": "5fa85f64-5717-4562-b3fc-2c963f66afa6",
      "playlist_item_id": "6fa85f64-5717-4562-b3fc-2c963f66afa6",
      "media_asset_id": "7fa85f64-5717-4562-b3fc-2c963f66afa6",
      "playlist_version": 3,
      "media_checksum": "checksum-from-assigned-playlist",
      "played_at": "2026-11-24T10:15:00Z",
      "played_complete_at": "2026-11-24T10:15:15Z"
    }
  ]
}
```

`events` must contain 1–100 entries. The TV generates one `event_id` per
playback and reuses it when retrying a report. `played_at` is required;
`played_complete_at` is optional for playback interrupted before completion.
Timestamps must include a timezone, and a supplied completion cannot precede
start. The server derives `screen_id`
from the authenticated credential and records `received_at` itself. The
response contains `stored_count` and `duplicate_count`; duplicate event IDs
for that screen are ignored. Events are retained independently of mutable
playlist, item, media, and screen records. These are device-reported events;
the backend does not independently verify that media was displayed.

```json
{"stored_count":1,"duplicate_count":0}
```

Errors: `401 INVALID_SCREEN_CREDENTIAL`, `401 SCREEN_DISCONNECTED`, or `404
SCREEN_NOT_FOUND` for authentication; `422` for invalid event data or an empty
or oversized batch.

### 12. Log out the screen

**Method/path:** `POST /api/v1/screens/logout`
**Authentication:** Screen credential Bearer token
**Required header:** `Authorization: Bearer <screen-credential>`
**Path/query/body:** None
**Success:** `204 No Content`

The endpoint revokes the credential used for the request by setting its
`revoked_at` and revokes the temporary admin session. Both records are retained
for history. It does not delete
the screen, playlist assignment, or synchronization state. After a successful
response, the TV clears the credential locally and returns to pairing. The
revoked credential cannot authenticate later requests. Errors include
`401 INVALID_SCREEN_CREDENTIAL`, `401 SCREEN_DISCONNECTED`, `404 SCREEN_NOT_FOUND`,
and `401 EXPIRED_SESSION` when the temporary session is missing or invalid.

## Media URLs, duration, and playback

The TV does not need an authenticated media API request to get playlist media
metadata. The assigned-playlist response includes `media_url` and `checksum`.
The URL is constructed as a Supabase public-object URL using the configured
storage bucket and `storage_path`. The public URL is intended for direct object
download; the backend does not return a signed read URL or an expiration for
this URL. A bucket must actually be configured as public for unauthenticated
download to succeed.

`item.duration_seconds` and `media.duration_seconds` are distinct nullable
values. The backend does not define an image default duration, fallback rule,
transition, shuffle, looping policy, or schedule. Playlist items are delivered
in ascending `position`. When an owner replaces a media asset with a video, the
backend sets each referencing playlist item's duration to the replacement
video's duration and increments those playlist versions. No playback behavior
beyond these stored fields is implemented in the API.

## Synchronization behavior and current gaps

- A new screen's sync row starts with `desired_revision=1` and
  `applied_revision=0` (`sync_status=PENDING`), requiring an initial full sync.
- Issuing or rotating a screen credential increments `desired_revision`, so a
  reconnecting TV fetches the current assigned content.
- Playlist assignment/removal, playlist updates/deletion, and media replacement
  for media used by an assigned playlist increment a screen's desired revision.
- `POST /screens/sync-check` returns the derived Boolean and current
  `desired_revision`; when sync is needed it sets `sync_status=SYNCING` and
  records `last_sync_started_at`. It does not return `applied_revision` or
  `sync_status`.
- `GET /screens/assigned-playlist` returns the current full playlist snapshot;
  there is no revision parameter, delta endpoint, ETag, or conditional request
  contract.
- The acknowledgment endpoint advances `applied_revision` only after the TV
  confirms a successfully applied revision; it does not accept a separate
  playback event or detailed failure report.
- Domain methods exist for `SYNCING`, `SYNCED`, and `FAILED`, but source search
  shows no application route/use case calls them. `SyncStatus` is not exposed in
  any screen-device response.
- No API accepts device error reports or manual sync commands,
  advertisement schedules, or a heartbeat body with device health details.

The TV sync loop is: check `need_sync`; when true, fetch
`/screens/assigned-playlist`, download/apply the playlist content, then submit
the applied revision to `/screens/sync-acknowledgments`. Check `need_sync`
again to detect a newer desired revision.

## App-user and management routes (not authenticated by TV credentials)

These routes may be used by the companion management app, but their
`Authorization` token must be an app-user Supabase access token, not a screen
credential.

| Method/path | Purpose | Body/response summary |
| --- | --- | --- |
| `GET /api/v1/screens/{screen_id}` | Read owned screen management details | Returns `id`, `screen_code`, `name`, `status`, `updated_at`, and `assigned_playlist` (playlist metadata/items with media IDs only), or `404 SCREEN_NOT_FOUND`. |
| `PATCH /api/v1/screens/{screen_id}` | Rename screen | Body `{"name":"..."}`; name is trimmed, length 1–255; returns screen identity/status/update timestamp. |
| `GET /api/v1/screens` | List owned screens | Query `filter_by_name` (optional, max 255), `page` (default 1, >=1), `limit` (default 20, 1–100). Paginated screen items include device model/version, last seen, and last successful sync timestamps. |
| `PUT /api/v1/screens/{screen_id}/playlist` | Assign/replace playlist | Body `{"playlist_id":"<uuid>"}`; returns assignment ID, screen/playlist IDs, and `assigned_at`. Same assignment is idempotent. |
| `DELETE /api/v1/screens/{screen_id}/playlist` | Remove assignment | Empty body; `204`; idempotent when already unassigned. |
| `POST /api/v1/screens/{screen_id}/disconnect` | Revoke active device credential | Empty body; `204`; idempotent when already disconnected. Screen data is kept. |
| `DELETE /api/v1/screens/{screen_id}` | Delete owned screen | Empty body; `204`; dependent credentials, sync state, and assignments cascade/delete. |

These operations are not callable with the screen credential. The disconnect
route is the supported management-side logout/deauthorization operation.

## Related app authentication routes

These are browser/app-user auth routes, not device-credential routes:

- `GET /api/v1/auth/google/request`: starts provider OAuth with PKCE and a
  short-lived HttpOnly state cookie; responds with a 307 redirect.
- `GET /api/v1/auth/google/callback`: consumes state and exchanges the code;
  successful callback sets an HttpOnly refresh-token cookie and redirects to
  the configured frontend. Provider errors use the shared application error
  envelope.
- `POST /api/v1/auth/refresh`: JSON body `{"refresh_token":"..."}`; returns
  `access_token`, rotated `refresh_token`, `token_type`, and nullable
  `expires_in`. Request schema requires a nonempty secret string. The backend
  does not expose a TV-specific OAuth or user-token endpoint.

## Capabilities not found in the current backend

The TV API does not provide:

- Fetching a sync manifest/delta or media changes by revision.
- Reporting playback progress, playback errors, device health, or manual sync.
- Fetching ad schedules, campaigns, playback configuration, or timing rules.
- Updating device model/app version or arbitrary screen configuration after
  registration.
- Refreshing a screen credential without going through a pairing session.
- Reading a screen's management record using only the screen credential.

Do not implement these client behaviors as if the current API supports them;
they require a backend contract that is not present in the inspected source.
