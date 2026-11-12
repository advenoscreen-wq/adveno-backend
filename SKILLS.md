# Adveno Backend Engineering Skills

> **Purpose:** This document defines the mandatory engineering standards
> for AI coding agents and human developers working on the Adveno
> backend MVP.
>
> **Project scope:** Adveno MVP is one internal screen and
> digital-signage management system controlling multiple Adveno TV
> devices. It includes screen/device management, centralized media
> management, playlists, playback configuration, cloud synchronization,
> offline playback support, and an internal Super Admin dashboard. There
> are no customer accounts, company workspaces, subscriptions, billing,
> or customer-facing mobile applications.

------------------------------------------------------------------------

## 1. Agent Operating Rules

You are an engineering agent working on a production-minded backend.
Your responsibility is to deliver correct, secure, tested, maintainable
changes --- not merely code that appears to work.

### 1.1 Before changing code

1.  Inspect the existing repository structure, `pyproject.toml`,
    configuration, application entry point, tests, migrations, `api.md`,
    Makefile, and CI workflows.
2.  Read the relevant use cases, domain models, ports/interfaces,
    adapters, and existing tests before proposing changes.
3.  Follow established conventions where they do not conflict with this
    document.
4.  Identify the affected layers and the tests/documentation that must
    change.
5.  Check whether the requested feature is within the approved MVP
    scope.
6.  If requirements are ambiguous in a way that affects security, data
    integrity, API behaviour, or architecture, ask a concise
    clarification instead of inventing behaviour.

### 1.2 While implementing

-   Make the smallest coherent change that fully solves the task.
-   Follow Clean Architecture and dependency inversion.
-   Keep business rules independent of FastAPI, SQLAlchemy, PostgreSQL,
    Supabase, and other frameworks.
-   Add or update tests with every implementation change.
-   Add or update database migrations when the schema changes.
-   Update `api.md` whenever an API is added or changed.
-   Update configuration examples and operational documentation when
    configuration or commands change.
-   Never silently weaken validation, authorization, test coverage, or
    security to make a test pass.

### 1.3 Logic-first development and minimal verification

**Priority: understand and implement the logic correctly. Do not spend
excessive time or tokens running checks.**

For each task:

1.  Read the relevant code and understand the existing flow before
    editing.
2.  Trace the affected business logic, state transitions, data ownership
    and failure cases.
3.  Implement the complete change consistently across the required
    layers.
4.  Review the changed code yourself for correctness, edge cases,
    security and Clean Architecture boundaries.
5.  Add or update the appropriate tests, but run only the smallest
    relevant verification.

**Minimal execution policy:** - Run one focused test command only when
verification is useful for the change. - Run one relevant quality
command only when the change may affect style, imports or static
correctness. - Do not automatically run unit tests, integration tests,
coverage, type checking, formatting, linting and pre-commit together
after every change. - Do not run the full test suite for a small,
isolated change. - Do not run coverage reports, Docker builds,
migrations, or Testcontainers unless the change actually requires
them. - Do not repeat successful checks. - If a check fails, inspect and
fix the underlying issue; rerun only the failed check or the smallest
relevant command. - For documentation-only changes, inspect the edited
documentation; no test suite is needed. - For straightforward code
changes, prefer careful code review and targeted verification over
running many tools.

**The agent must not equate the number of checks with correctness.**
Spend effort reasoning through the implementation and validating the
logic. Tests are required to be written/updated according to the testing
rules, but broad test execution is reserved for significant changes,
explicit requests, or release verification.

At completion, briefly report the implementation and only the
verification actually performed. Never claim a check passed unless it
was run.

------------------------------------------------------------------------

## 2. Product and Backend Scope

Adveno is one internal management system controlling multiple Adveno TV
screens. The backend supports:

-   **Screen management:** register screens, generate stable unique
    Screen IDs, QR pairing, secure device authentication, screen
    listing/details, online/offline status, last successful
    synchronization, unpairing and deactivation.
-   **Media management:** upload images and MP4 videos, store media in
    cloud object storage, browse/preview/search/delete media, and
    maintain one centralized media library.
-   **Playlist management:** create/delete/rename/edit playlists,
    add/remove/reorder media, configure image display duration, and
    assign one playlist to multiple screens.
-   **Playback configuration:** persist playback settings such as
    orientation and fit/fill/crop display mode; support continuous
    playback and automatic playback after device restart.
-   **Cloud synchronization:** track playlist/media versions and
    synchronization status, identify changed assets, avoid downloading
    unchanged files, and switch to an updated playlist only after
    required media is ready.
-   **Offline playback support:** allow TVs to retain the last
    successfully synchronized playlist and downloaded media, continue
    playback offline, and resume synchronization after connectivity
    returns.
-   **Internal admin dashboard:** allow the Super Admin to manage
    screens, media, playlists, assignments and synchronization status.

### Explicitly out of scope

-   Customer registration/login or customer management.
-   Company workspaces, company registration or tenant-specific storage.
-   Customer mobile application.
-   Subscription plans, billing or payment integration.
-   Customer-specific permissions or customer-facing features.

The MVP has one privileged administrator role: `SUPER_ADMIN`. Do not add
additional roles or multi-tenancy without explicit approval.

Do not assume the backend itself plays media. The Android TV app is
responsible for local media storage and playback; the backend stores
authoritative metadata, configuration, assignments and synchronization
state. Actual media bytes belong in configured object storage, not
PostgreSQL.

------------------------------------------------------------------------

## 3. Required Technology

Use the following stack unless the project owner explicitly approves a
change.

  ---------------------------------------------------------------------
  Concern                            Technology
  ---------------------------------- ----------------------------------
  Language                           Python

  API framework                      FastAPI

  Architecture                       Clean Architecture

  Package/dependency manager         `uv`

  Database                           PostgreSQL

  ORM                                SQLAlchemy 2.x

  Migrations                         Alembic

  Validation / DTOs                  Pydantic

  Testing                            pytest

  Integration database               PostgreSQL via Testcontainers or
                                     Docker Compose

  Local development                  Docker + Docker Compose

  Git hooks                          pre-commit

  CI/CD                              GitHub Actions (or the
                                     repository's approved CI provider)

  API documentation                  `api.md` plus generated OpenAPI
                                     documentation

  Logging                            Python standard logging with
                                     structured output where practical
  ---------------------------------------------------------------------

Do not add Redis, Celery, a message broker, or another database unless a
confirmed requirement justifies it.

### 3.1 Supabase and PostgreSQL

If Supabase is selected as the managed PostgreSQL provider:

-   Treat PostgreSQL as the database technology; Supabase is the managed
    platform/provider.
-   The FastAPI backend remains the owner of business logic and
    authorization.
-   Do not expose Supabase service-role keys or database credentials to
    the TV app or browser.
-   Do not allow clients to bypass backend business rules by writing
    directly to privileged tables.
-   Keep secrets in environment variables or the approved secret
    manager.
-   Use least-privilege database credentials.
-   Document any Supabase-specific dependency instead of coupling the
    domain/application layers to Supabase SDKs.

------------------------------------------------------------------------

## 4. Clean Architecture

The project MUST follow Clean Architecture with explicit separation of:

1.  **Drivers** --- entry points and delivery mechanisms, such as
    FastAPI routes and application startup.
2.  **Domain** --- core business entities, value objects, domain rules,
    and domain errors.
3.  **Application** --- use cases, application orchestration,
    ports/interfaces, commands, queries, and application exceptions.
4.  **Adapters / Infrastructure** --- implementations of ports, such as
    SQLAlchemy repositories, database sessions, external service
    clients, and persistence mappings.
5.  **Tests** --- unit and integration tests, mirroring the production
    package structure.

### 4.1 Dependency rule

Dependencies point inward:

-   Drivers may depend on Application and on the code required to
    assemble the application.
-   Adapters/Infrastructure implement interfaces defined by inner
    layers.
-   Application depends on Domain and its own abstractions/ports.
-   Domain depends on no outer layer.
-   Domain and Application must not import FastAPI, SQLAlchemy, Pydantic
    HTTP DTOs, or provider SDKs.

The Domain layer must remain framework-independent.

### 4.2 Suggested project structure

Use this as the default structure. Adapt names to the actual codebase
while preserving the layer boundaries.

``` text
adveno-backend/
├── pyproject.toml
├── uv.lock
├── README.md
├── api.md
├── Makefile
├── .python-version
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── compose.yaml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── src/
│   └── adveno/
│       ├── __init__.py
│       ├── main.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py
│       │   └── logging.py
│       ├── drivers/
│       │   └── http/
│       │       ├── __init__.py
│       │       ├── app.py
│       │       ├── dependencies.py
│       │       ├── exception_handlers.py
│       │       ├── middleware/
│       │       └── v1/
│       │           ├── router.py
│       │           ├── admin_auth/
│       │           │   ├── routes.py
│       │           │   └── schemas.py
│       │           └── screens/
│       │               ├── routes.py
│       │               └── schemas.py
│       ├── domain/
│       │   ├── common/
│       │   │   ├── exceptions.py
│       │   │   └── value_objects.py
│       │   ├── screens/
│       │   │   ├── entities.py
│       │   │   ├── value_objects.py
│       │   │   ├── enums.py
│       │   │   └── exceptions.py
│       │   └── administrators/
│       │       ├── entities.py
│       │       └── value_objects.py
│       ├── application/
│       │   ├── common/
│       │   │   ├── exceptions.py
│       │   │   ├── result.py
│       │   │   └── ports/
│       │   ├── screens/
│       │   │   ├── dto.py
│       │   │   ├── commands.py
│       │   │   ├── queries.py
│       │   │   ├── ports.py
│       │   │   └── use_cases/
│       │   │       ├── register_screen.py
│       │   │       ├── create_pairing_session.py
│       │   │       ├── pair_screen.py
│       │   │       ├── receive_heartbeat.py
│       │   │       ├── list_screens.py
│       │   │       ├── get_screen_details.py
│       │   │       ├── rename_screen.py
│       │   │       ├── unpair_screen.py
│       │   │       ├── deactivate_screen.py
│       │   │       └── reactivate_screen.py
│       │   └── administrators/
│       │       ├── ports.py
│       │       └── use_cases/
│       ├── adapters/
│       │   ├── persistence/
│       │   │   └── sqlalchemy/
│       │   │       ├── database.py
│       │   │       ├── models/
│       │   │       ├── mappers/
│       │   │       └── repositories/
│       │   ├── security/
│       │   │   ├── password_hasher.py
│       │   │   └── token_service.py
│       │   └── external/
│       │       └── services/
│       └── bootstrap/
│           ├── container.py
│           └── dependencies.py
├── tests/
│   ├── unit/
│   │   └── adveno/
│   │       ├── domain/
│   │       ├── application/
│   │       └── adapters/
│   ├── integration/
│   │   └── adveno/
│   │       ├── adapters/
│   │       │   └── persistence/
│   │       │       └── sqlalchemy/
│   │       │           └── repositories/
│   │       └── drivers/
│   │           └── http/
│   │               └── v1/
│   │                   ├── admin_auth/
│   │                   └── screens/
│   ├── conftest.py
│   └── factories/
├── scripts/
└── .github/
    └── workflows/
        └── ci.yml
```

### 4.3 Feature organisation

Organise code by business capability within each layer. Avoid a single
giant `services.py`, `repositories.py`, or `utils.py` containing
unrelated features.

A use case should have one clear responsibility. For example:

-   `RenameScreen` changes a screen's display name.
-   `UnpairScreen` revokes the existing device pairing and credentials.
-   `ReceiveHeartbeat` validates an authenticated device heartbeat and
    updates its last-seen information.

Do not combine unrelated operations into one use case merely to reduce
the number of files.

### 4.4 Composition root

Construct concrete implementations in `bootstrap/` or the approved
composition root:

-   Database session factory.
-   Repository implementations.
-   Security services.
-   Use-case dependencies.
-   External service clients.

Do not instantiate SQLAlchemy repositories or provider clients inside
domain entities or use cases. Inject their interfaces.

------------------------------------------------------------------------

## 5. Domain Layer Rules

The Domain layer contains the business model and rules.

### MUST

-   Use plain Python classes/dataclasses for domain entities and value
    objects.
-   Represent domain state explicitly using enums/value objects where
    appropriate.
-   Validate business invariants in the domain model or domain policies.
-   Keep entities independent from persistence models.
-   Use domain-specific exceptions for violated business rules.
-   Make state transitions explicit.

### MUST NOT

-   Import FastAPI, SQLAlchemy, Pydantic, or external SDKs.
-   Return HTTP responses or HTTP status codes.
-   Read environment variables.
-   Open database connections.
-   Perform network or filesystem operations.
-   Contain request/response schemas.

### Example concepts

Potential domain concepts for the current MVP include:

-   `Screen`
-   `ScreenId`
-   `ScreenStatus`
-   `PairingSession`
-   `PairingToken`
-   `DeviceCredential`
-   `Administrator`
-   `AuditEvent`

Only create concepts that represent real domain requirements.

------------------------------------------------------------------------

## 6. Application Layer Rules

The Application layer coordinates business operations. It contains use
cases and the interfaces they require.

### 6.1 Use-case responsibilities

Each use case MUST:

1.  Accept an explicit command/query or clearly defined input DTO.
2.  Validate application-level preconditions.
3.  Load required entities through repository ports.
4.  Apply or invoke domain behaviour.
5.  Persist changes through ports.
6.  Invoke required external-service ports.
7.  Return a framework-independent result/DTO.
8.  Raise documented application/domain exceptions for expected
    failures.

Keep use cases focused. Do not put HTTP parsing, SQL queries, or
framework-specific response handling here.

### 6.2 Ports and interfaces

Define interfaces in the inner layer that needs them. Examples:

-   `ScreenRepository`
-   `PairingSessionRepository`
-   `AdministratorRepository`
-   `AuditLogRepository`
-   `PasswordHasher`
-   `TokenService`
-   `Clock`
-   `DeviceCredentialService`

Use Python `Protocol` or abstract base classes consistently. Do not
define interfaces for every trivial function without a meaningful
substitution/testing boundary.

### 6.3 Transaction boundaries

Make transaction ownership explicit.

-   A use case should have a clear unit-of-work boundary.
-   Repository methods should not commit independently unless the
    repository contract explicitly requires it.
-   Prefer committing once after a complete business operation.
-   Roll back on failure.
-   Ensure pairing, unpairing, deactivation and credential revocation
    are transactionally safe.
-   Avoid partially completed state transitions.

### 6.4 Idempotency and concurrency

For operations that may be retried by devices or clients:

-   Make heartbeat handling safe to retry.
-   Make pairing-token consumption atomic and single-use.
-   Prevent two concurrent requests from successfully consuming the same
    pairing token.
-   Use database constraints and appropriate transaction/locking
    strategies where required.
-   Consider duplicate request behaviour explicitly.
-   Do not rely only on frontend validation for uniqueness or state
    transitions.

------------------------------------------------------------------------

## 7. Exception Handling and Error Contracts

**Expected application exceptions MUST be defined in the Application
layer.** Domain invariants may also have domain-specific exceptions in
the Domain layer. Drivers translate these exceptions into HTTP
responses.

Do not raise `HTTPException` from Domain or Application.

### 7.1 Exception structure

Use a common application exception base, for example:

``` python
class ApplicationError(Exception):
    code: str
    message: str

    def __init__(self, message: str, code: str) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ResourceNotFoundError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass


class UnauthorizedError(ApplicationError):
    pass


class ForbiddenError(ApplicationError):
    pass


class ValidationError(ApplicationError):
    pass


class PairingTokenExpiredError(ApplicationError):
    pass


class PairingTokenAlreadyUsedError(ApplicationError):
    pass
```

The exact classes may be refined to match the domain. Avoid creating
many near-identical exception types without a meaningful reason.

### 7.2 System error code and HTTP status code

Every API error response MUST preserve both:

-   A stable application/system error code, such as `SCREEN_NOT_FOUND`.
-   The corresponding HTTP status code, such as `404`.

Do not use the HTTP status code as the only machine-readable error
identifier.

Example error response:

``` json
{
  "error": {
    "code": "SCREEN_NOT_FOUND",
    "message": "The requested screen was not found.",
    "status_code": 404
  }
}
```

The driver/HTTP exception handler maps application exceptions to HTTP
status codes. Keep the mapping centralised and documented.

Suggested mapping:

  ---------------------------------------------------------------------
  Application condition                                     HTTP status
  ----------------------------- ---------------------------------------
  Invalid request data                                              422

  Missing/invalid                                                   401
  authentication                

  Authenticated but not                                             403
  permitted                     

  Resource not found                                                404

  Duplicate/conflicting state                                       409

  Expired pairing token             410 or 400, chosen consistently and
                                                             documented

  Rate limit exceeded                                               429

  Unexpected internal failure                                       500

  Temporarily unavailable                                           503
  dependency                    
  ---------------------------------------------------------------------

Use a consistent error envelope for all application-level API errors. Do
not expose stack traces, SQL details, secrets, token values, or internal
provider responses to clients.

### 7.3 Logging exceptions

-   Log unexpected exceptions with stack traces on the server.
-   Do not log passwords, bearer tokens, pairing secrets, device
    credentials, or full sensitive request bodies.
-   Include request/correlation IDs where available.
-   Return safe, generic messages for unexpected failures.

------------------------------------------------------------------------

## 8. Drivers / FastAPI Layer

Drivers translate external input into application calls and application
results into protocol responses.

### MUST

-   Keep routes thin.
-   Validate HTTP input using Pydantic request schemas.
-   Authenticate and authorise requests before protected operations.
-   Call use cases through dependency injection.
-   Convert application DTOs/results into response schemas.
-   Use central exception handlers.
-   Use explicit response models and status codes.
-   Version APIs, initially under `/api/v1`.
-   Keep OpenAPI tags and summaries meaningful.
-   Define pagination, sorting and filtering consistently.
-   Avoid leaking database models directly in API responses.

### MUST NOT

-   Put business rules in route functions.
-   Execute SQL queries in route functions.
-   Import ORM models into response schemas.
-   Construct repositories independently in each endpoint.
-   Catch every exception and return `200 OK`.
-   Return raw exception messages for unexpected errors.

### API conventions

-   Use nouns for resource paths.
-   Use HTTP methods consistently.
-   Use appropriate status codes.
-   Keep naming consistent (`screen_id`, `created_at`, etc.).
-   Use UTC timestamps in ISO 8601 format.
-   Define pagination limits and defaults.
-   Validate all path, query and body inputs.
-   Keep authentication requirements explicit.

Example route naming:

``` text
POST   /api/v1/admin/auth/login
POST   /api/v1/admin/auth/logout
GET    /api/v1/admin/screens
GET    /api/v1/admin/screens/{screen_id}
PATCH  /api/v1/admin/screens/{screen_id}
POST   /api/v1/admin/screens/{screen_id}/unpair
POST   /api/v1/admin/screens/{screen_id}/deactivate
POST   /api/v1/admin/screens/{screen_id}/reactivate
POST   /api/v1/device/pairing-sessions
POST   /api/v1/device/pair
POST   /api/v1/device/heartbeat
```

These are illustrative names, not permission to implement every endpoint
without confirming the approved API contract.

------------------------------------------------------------------------

## 9. `api.md` Is Mandatory

The root-level `api.md` is the maintained API reference for frontend and
device developers.

**Whenever an API is added, removed, renamed, or changed, update
`api.md` in the same change.** This is not optional and must not be
deferred to a later task.

For every endpoint document:

-   HTTP method and full path.
-   Purpose.
-   Authentication/authorization requirement.
-   Required headers.
-   Path parameters.
-   Query parameters.
-   Request body schema and example.
-   Successful response status and body example.
-   Possible error status codes and system error codes.
-   Validation rules.
-   Relevant business rules.
-   Pagination/filter/sort behaviour, if applicable.
-   Idempotency/retry behaviour, if applicable.
-   Notes about device credential or pairing-token handling, without
    documenting actual secrets.

Also document shared conventions:

-   Base URL and API version.
-   Authentication scheme.
-   Timestamp format/time zone.
-   Pagination format.
-   Standard success/error response envelopes.
-   Common system error codes.
-   Device authentication requirements.
-   Pairing-token lifecycle and heartbeat expectations.

Do not document secrets, production credentials, or real tokens.

### API change checklist

Before completing an API-related task, verify:

-   [ ] FastAPI route and response model updated.
-   [ ] Application use case updated or created.
-   [ ] Unit tests updated.
-   [ ] API integration tests updated.
-   [ ] `api.md` updated with request and response examples.
-   [ ] OpenAPI output remains valid.
-   [ ] Authentication and authorization are tested.

------------------------------------------------------------------------

## 10. Database and Repository Rules

### 10.1 SQLAlchemy

-   Use SQLAlchemy 2.x style APIs.
-   Prefer explicit typed mappings.
-   Keep ORM models in Infrastructure/Adapters.
-   Keep domain entities separate from ORM models.
-   Use explicit mapper functions to convert between ORM and domain
    representations.
-   Use parameterised ORM queries; never build SQL using untrusted
    string interpolation.
-   Avoid N+1 queries.
-   Select only required data where practical.
-   Use database constraints for important invariants.
-   Use timezone-aware UTC timestamps.
-   Use explicit indexes for frequently queried fields when justified.

### 10.2 Repository pattern

Repository interfaces belong in Application (or the inner layer that
requires them). SQLAlchemy implementations belong in
Adapters/Infrastructure.

A repository should:

-   Encapsulate persistence details.
-   Return domain entities or application-approved
    persistence-independent values.
-   Translate persistence concerns where necessary.
-   Avoid exposing SQLAlchemy sessions or ORM objects to use cases.
-   Have a clear transaction contract.
-   Raise meaningful errors or allow well-defined persistence exceptions
    to be translated at the adapter boundary.

Do not create a generic repository abstraction that hides useful query
behaviour or forces every query into an unsuitable CRUD interface.

### 10.3 Media, playlists and synchronization data

For the expanded MVP:

-   Store media metadata and object-storage keys in PostgreSQL; store
    image/video bytes in object storage (for example, the selected
    Supabase Storage or S3-compatible provider).
-   Keep the media library centralized. Do not add customer/company
    ownership columns or tenant scoping.
-   Model playlist ordering explicitly with a playlist-item
    position/order field and a uniqueness constraint appropriate to each
    playlist.
-   Model playlist-to-screen assignment as a relationship table so one
    playlist can be assigned to multiple screens and assignments can be
    queried in both directions.
-   Persist playback configuration at the correct level (playlist item,
    playlist, or screen) based on the agreed product rule; do not guess
    precedence.
-   Track synchronization state/version separately from the device's
    last successful synchronization timestamp.
-   Design synchronization so the TV can identify changed media and
    avoid re-downloading unchanged files. Use stable media identifiers
    and content hashes/checksums where appropriate.
-   Preserve the last successfully synchronized/active playlist until
    the replacement playlist and its required media are ready on the TV.
-   Do not store device-local cached media bytes in PostgreSQL. The TV
    owns its local cache.

### 10.3 Migrations

-   Every schema change requires an Alembic migration.
-   Review generated migrations manually.
-   Never assume autogenerated migrations are correct.
-   Preserve existing data unless a destructive migration is explicitly
    approved.
-   Add constraints and indexes deliberately.
-   Test migrations against a real PostgreSQL instance.
-   Ensure migrations can be applied from the current baseline.
-   Document any manual deployment or backfill step.
-   Never edit an already-applied migration as a way to change
    production schema; create a new migration.

------------------------------------------------------------------------

## 11. Testing Strategy --- Mandatory

Testing is a core delivery requirement, but test execution should be
focused to avoid redundant commands and unnecessary agent/tool tokens.

Use **pytest** for all automated tests.

### 11.1 Required coverage by component

  ---------------------------------------------------------------------
  Component                          Required test type
  ---------------------------------- ----------------------------------
  Every use case                     Unit test

  Every domain entity with behaviour Unit test

  Every domain rule/state transition Unit test

  Every external-service adapter     Unit test with mocked dependency +
                                     integration/contract test when
                                     practical

  Every repository implementation    Integration test

  Every API endpoint                 Integration test

  Authentication and authorization   Unit and API integration tests

  Database migrations                Migration integration test

  Pairing-token security and         Unit and integration tests
  lifecycle                          
  ---------------------------------------------------------------------

Do not consider a feature complete when the implementation exists but
the required tests are missing.

### 11.2 Unit tests

Unit tests MUST:

-   Test one behaviour at a time.
-   Be deterministic and independent of external services.
-   Use fakes or mocks for ports.
-   Verify successful behaviour and failure cases.
-   Verify important interactions with dependencies.
-   Cover boundary conditions and invalid state transitions.
-   Avoid depending on test execution order.
-   Avoid requiring Docker or a live database.

**Every use case must have unit tests.** Cover at least the normal path,
relevant validation/business-rule failures, and dependency failures.

For external-service adapters, unit-test request construction, response
mapping, timeout handling, retry/error translation and malformed
responses using mocked HTTP/client dependencies as applicable.

### 11.3 Integration tests

Integration tests verify real boundaries.

**Every repository implementation must have integration tests against
PostgreSQL.**

**Every API endpoint must have integration tests through the FastAPI
application**, using a real test database where database behaviour is
part of the endpoint.

Test important behaviour such as:

-   Persisting and retrieving records.
-   Unique constraints and foreign keys.
-   Transaction commit and rollback.
-   Filtering, ordering and pagination.
-   Authentication and authorization.
-   Request validation.
-   Response schema and status code.
-   Error envelope and system error code.
-   Pairing-token expiry and single-use behaviour.
-   Credential revocation after unpairing/deactivation.
-   Heartbeat timestamp updates and online/offline rules.

Use Testcontainers for PostgreSQL when the local/CI environment supports
Docker. A dedicated PostgreSQL test service in Docker Compose is also
acceptable. Do not substitute SQLite for PostgreSQL integration tests
when PostgreSQL-specific behaviour, constraints, types or queries
matter.

### 11.4 Test folder structure

The test folders MUST mirror the production package structure.

Keep separate `unit` and `integration` roots, but preserve the same
package paths under each.

Example:

``` text
src/adveno/application/screens/use_cases/rename_screen.py

tests/
├── unit/
│   └── adveno/
│       └── application/
│           └── screens/
│               └── use_cases/
│                   └── test_rename_screen.py
└── integration/
    └── adveno/
        └── drivers/
            └── http/
                └── v1/
                    └── screens/
                        └── test_rename_screen_api.py
```

Repository example:

``` text
src/adveno/adapters/persistence/sqlalchemy/repositories/screen_repository.py

tests/
└── integration/
    └── adveno/
        └── adapters/
            └── persistence/
                └── sqlalchemy/
                    └── repositories/
                        └── test_screen_repository.py
```

Do not place all tests in one flat directory.

### 11.5 Test naming and fixtures

-   Name test files `test_*.py`.
-   Name test functions `test_<expected_behaviour>`.
-   Use descriptive fixtures.
-   Keep shared fixtures in the nearest appropriate `conftest.py`.
-   Use factories/builders for complex test objects.
-   Keep test data isolated between tests.
-   Clean up database state reliably.
-   Avoid excessive mocking that makes tests pass while real integration
    is broken.

### 11.6 Testcontainers

Use Testcontainers when a test needs a real PostgreSQL instance and a
Docker daemon is available.

-   Pin or control the PostgreSQL image version to match the supported
    development/production major version.
-   Wait for readiness before connecting.
-   Apply Alembic migrations before integration tests.
-   Use isolated databases/schemas or reliable cleanup.
-   Close containers and connections after tests.
-   Make CI Docker requirements explicit.

If Testcontainers is unsuitable for the repository's CI environment, use
a dedicated PostgreSQL service container in the CI workflow or Docker
Compose.

### 11.7 Coverage

-   Configure coverage reporting with pytest-cov.
-   Aim for at least 80% overall coverage as an initial quality gate.
-   Prioritise 100% coverage of critical business rules and
    security-sensitive paths where practical.
-   Do not write meaningless tests solely to increase coverage.
-   Do not exclude production code from coverage without documenting the
    reason.

------------------------------------------------------------------------

## 12. External Services and Reliability

All external services must be accessed through adapters implementing
inner-layer ports.

### Rules

-   Set explicit connection and read timeouts.
-   Handle network failures, timeouts and malformed responses.
-   Translate provider-specific errors into stable application-level
    errors where appropriate.
-   Retry only operations that are safe to retry.
-   Use bounded retries and backoff when retries are justified.
-   Do not retry non-idempotent operations blindly.
-   Do not log credentials or sensitive payloads.
-   Make external dependencies replaceable in tests.
-   Keep provider SDKs out of Domain and Application.

For each external service adapter:

1.  Unit-test behaviour with mocks/fakes.
2.  Test error and timeout handling.
3.  Add integration or contract tests when a real service or a local
    compatible service is available.
4.  Document required environment variables and local-development
    behaviour.

Avoid introducing an external service when PostgreSQL and FastAPI can
meet the current MVP requirement.

------------------------------------------------------------------------

## 13. Authentication, Authorization and Security

Security-sensitive operations must be enforced by the backend. Frontend
visibility is not authorization.

### 13.1 Super Admin

-   The initial MVP supports one privileged administrator role:
    `SUPER_ADMIN`.
-   Do not implement Admin, Support Staff, customer roles or
    multi-tenant roles unless approved.
-   Protect every screen-management endpoint with administrator
    authentication and authorization.
-   Use secure password hashing such as Argon2id through a maintained
    library.
-   Never store plaintext passwords.
-   Never hardcode credentials or signing secrets.
-   Define token expiry and revocation behaviour.
-   Validate issuer, audience, expiry and signature for tokens where
    applicable.
-   Use HTTPS in deployed environments.

### 13.2 Device identity and credentials

-   A Screen ID is a stable identifier, not a secret or authentication
    credential.
-   Pairing tokens must be short-lived, single-use, unpredictable and
    validated by the backend.
-   Store only a secure hash of a pairing secret/token where the design
    allows it.
-   Consume pairing tokens atomically.
-   Issue device credentials only after successful pairing.
-   Store device credentials securely on the TV.
-   Revoke old credentials on unpairing and deactivation.
-   Reject heartbeat and other device requests using revoked, expired or
    invalid credentials.
-   Never trust a Screen ID supplied by a client as proof of identity.

### 13.3 Input and operational security

-   Validate all incoming data.
-   Apply rate limiting to sensitive authentication and pairing
    endpoints.
-   Use safe CORS configuration.
-   Avoid exposing internal exception details.
-   Protect secrets using environment variables/secret management.
-   Keep `.env` files out of version control.
-   Provide `.env.example` with placeholder values only.
-   Apply least privilege to database and service credentials.
-   Audit important administrator actions.

------------------------------------------------------------------------

## 14. Screen Status and Heartbeat Rules

Heartbeat and status behaviour must be explicit and consistent.

-   Store the latest accepted heartbeat timestamp in UTC.
-   Derive or update online/offline state using a documented timeout.
-   Make timeout configurable rather than scattering a hardcoded value
    across the codebase.
-   Handle delayed and duplicate heartbeat requests safely.
-   Do not allow unauthenticated clients to update a screen's heartbeat.
-   Record useful device metadata only when required by the MVP.
-   On network recovery, the TV should resume heartbeat reporting.
-   Define how a deactivated or unpaired device behaves when it
    reconnects.

Avoid relying on a process-local in-memory timer for global device
status. Status must remain correct across backend restarts and multiple
backend instances. Use database timestamps and a reliable
scheduled/reconciliation strategy if persisted status updates are
required.

------------------------------------------------------------------------

## 15. Audit Logging

Important screen-management actions must be auditable.

At minimum, consider recording:

-   Screen registered.
-   Pairing session created.
-   Screen paired.
-   Screen renamed.
-   Screen unpaired.
-   Device credentials revoked.
-   Screen deactivated.
-   Screen reactivated.
-   Authentication/security events where appropriate.

Audit records should include, when available:

-   Event/action type.
-   Actor administrator ID or system/device actor.
-   Target screen ID.
-   Timestamp in UTC.
-   Outcome.
-   Safe metadata needed for investigation.
-   Request/correlation ID.

Do not store passwords, tokens, credential secrets, or unnecessary
personal data in audit records.

Audit history should be append-only through normal application
behaviour. Do not provide ordinary API operations that silently rewrite
or delete audit history.

------------------------------------------------------------------------

## 16. Configuration and Environment Management

-   Use typed settings, preferably Pydantic Settings.
-   Read configuration from environment variables.
-   Validate required settings at application startup.
-   Separate development, test and production configuration.
-   Never commit secrets.
-   Keep `.env.example` updated whenever a new setting is introduced.
-   Use safe defaults for local development only.
-   Fail fast when required production settings are missing.

Document settings such as:

-   Environment name.
-   API host/port.
-   Database URL.
-   Database pool configuration.
-   JWT signing/verification configuration.
-   Token expiry settings.
-   Pairing-token TTL.
-   Heartbeat timeout.
-   CORS allowed origins.
-   Logging level.
-   External-service URLs and credentials, if any.

Never use a production database for automated tests.

------------------------------------------------------------------------

## 17. Docker and Docker Compose

Docker and Docker Compose are the standard local development
environment.

### Requirements

-   Provide a reproducible Dockerfile for the API.
-   Provide a Compose file for local API and PostgreSQL development.
-   Use health checks for services where practical.
-   Persist local PostgreSQL data in a named volume.
-   Use environment variables rather than embedding secrets in images.
-   Avoid running the application as root in production images where
    practical.
-   Keep development reload behaviour separate from production
    execution.
-   Ensure migrations can be run explicitly.
-   Document startup, shutdown, logs and reset commands.

A typical local environment should allow a developer to clone the
repository, install/run the required tools, configure `.env`, and start
the backend and database with a small number of commands.

------------------------------------------------------------------------

## 18. `uv` Package Management

Use `uv` for Python dependency and environment management.

### Rules

-   Use `pyproject.toml` as the project/dependency configuration.
-   Commit `uv.lock`.
-   Use `uv add` to add runtime dependencies.
-   Use `uv add --dev` for development/test dependencies.
-   Use `uv sync` to install locked dependencies.
-   Use `uv run` to execute tools and application commands.
-   Do not mix pip, Poetry, Pipenv or another package manager into the
    workflow.
-   Do not manually edit `uv.lock`.
-   Update the lockfile whenever dependencies change.
-   Pin supported Python versions in project configuration.

Example:

``` bash
uv add fastapi sqlalchemy pydantic-settings
uv add --dev pytest pytest-cov pytest-asyncio httpx ruff mypy pre-commit
uv sync --all-groups
```

Adjust dependency groups to the actual `pyproject.toml` configuration.

------------------------------------------------------------------------

## 19. Code Quality and Style

Use automated tools consistently.

Recommended baseline:

-   Ruff for linting and formatting.
-   Mypy or the repository-approved type checker.
-   Pytest and pytest-cov.
-   Pre-commit for local hooks.

### Coding standards

-   Add type hints to public functions, methods and interfaces.
-   Prefer small functions with clear responsibilities.
-   Use descriptive names.
-   Avoid unexplained abbreviations.
-   Avoid unnecessary inheritance and overengineering.
-   Avoid mutable global state.
-   Use `pathlib` for filesystem paths.
-   Use timezone-aware UTC datetimes.
-   Prefer explicit error handling.
-   Keep comments focused on why, not what.
-   Remove dead code and unused imports.
-   Do not suppress type/lint errors without a clear reason and narrow
    scope.
-   Avoid broad `except Exception` blocks except at a deliberate
    process/HTTP boundary where unexpected errors are logged and safely
    handled.

------------------------------------------------------------------------

## 20. Pre-commit Hooks

Configure and use pre-commit.

At minimum, include hooks for:

-   Trailing whitespace.
-   End-of-file newline.
-   YAML/TOML/JSON validation where supported.
-   Ruff linting.
-   Ruff formatting.
-   Basic merge-conflict detection.
-   Secret detection where available and approved.

Requirements:

-   Commit `.pre-commit-config.yaml`.
-   Document installation and execution.
-   Developers should install hooks locally.
-   CI must run the same quality checks so bypassing local hooks does
    not bypass quality gates.

Typical setup:

``` bash
uv add --dev pre-commit
uv run pre-commit install
uv run pre-commit run --all-files
```

Do not treat pre-commit as a replacement for tests or CI.

------------------------------------------------------------------------

## 21. CI/CD

Use the repository's approved CI/CD system, initially GitHub Actions if
hosted on GitHub.

### Pull request / CI checks

The pipeline should:

1.  Check out the repository.
2.  Install the supported Python version and `uv`.
3.  Install locked dependencies.
4.  Run Ruff linting.
5.  Check formatting.
6.  Run type checking if configured.
7.  Run unit tests.
8.  Start PostgreSQL (service container or Testcontainers).
9.  Apply migrations.
10. Run repository and API integration tests.
11. Generate coverage output.
12. Fail the pipeline when required checks fail.

### Deployment

-   Deploy only from approved branches/tags/environments according to
    repository policy.
-   Keep production secrets in CI/CD secret storage.
-   Do not put secrets in workflow files.
-   Run database migrations as a controlled deployment step.
-   Avoid automatically running destructive migrations.
-   Provide health checks and a rollback/recovery plan.
-   Keep deployment permissions least-privileged.

Feature branches are managed by the developer. **The agent must not
create, rename, switch, merge, or delete feature branches unless
explicitly instructed.** Work within the branch/environment already
provided.

------------------------------------------------------------------------

## 22. Makefile

Maintain a root `Makefile` with short, discoverable commands. The
following is a baseline; adapt command names to the actual project
configuration.

``` makefile
.PHONY: help install dev up down logs shell test test-unit test-integration \
        test-cov lint format format-check typecheck check migrate migration \
        pre-commit pre-commit-all clean

help:
    @echo "install             Install locked dependencies"
    @echo "dev                 Run API locally"
    @echo "up                  Start Docker Compose services"
    @echo "down                Stop Docker Compose services"
    @echo "logs                Follow service logs"
    @echo "test                Run all tests"
    @echo "test-unit           Run unit tests"
    @echo "test-integration    Run integration tests"
    @echo "test-cov            Run tests with coverage"
    @echo "lint                Run Ruff lint"
    @echo "format              Format source and tests"
    @echo "format-check        Check formatting without changes"
    @echo "typecheck           Run static type checking"
    @echo "check               Run focused lint/format checks"
    @echo "full-check          Run comprehensive checks (optional)"
    @echo "migrate             Apply database migrations"
    @echo "migration           Create an Alembic migration"
    @echo "pre-commit          Run pre-commit on changed files"
    @echo "pre-commit-all      Run pre-commit on all files"
    @echo "clean               Remove local cache artifacts"

install:
    uv sync --all-groups

dev:
    uv run uvicorn adveno.main:app --reload --host 0.0.0.0 --port 8000

up:
    docker compose up --build -d

down:
    docker compose down

logs:
    docker compose logs -f

shell:
    docker compose exec api /bin/sh

test:
    uv run pytest

test-unit:
    uv run pytest tests/unit

test-integration:
    uv run pytest tests/integration

test-cov:
    uv run pytest --cov=adveno --cov-report=term-missing --cov-report=xml

lint:
    uv run ruff check .

format:
    uv run ruff format .

format-check:
    uv run ruff format --check .

typecheck:
    uv run mypy src

# Focused default quality check; run tests separately for the affected area.
check: lint format-check

# Optional comprehensive command for release/explicit full verification:
full-check: lint format-check typecheck test



migrate:
    uv run alembic upgrade head

migration:
    @test -n "$(name)" || (echo "Usage: make migration name='description'"; exit 1)
    uv run alembic revision --autogenerate -m "$(name)"

pre-commit:
    uv run pre-commit run

pre-commit-all:
    uv run pre-commit run --all-files

clean:
    rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml
```

Important: - Ensure the Uvicorn import path matches the actual package
layout. - Ensure pytest discovers tests under the configured paths. -
Ensure integration tests have a running PostgreSQL service. - Do not
make `check` silently skip a required tool. - If type checking is not
configured, either configure it or remove the command until it is.

------------------------------------------------------------------------

## 23. API and Database Documentation

Keep the following documentation accurate:

-   `README.md`: project overview, prerequisites, setup, commands and
    local development.
-   `api.md`: endpoint contract and examples; update on every API
    change.
-   `.env.example`: all required configuration keys with safe
    placeholders.
-   Migration files: schema evolution history.
-   Architecture notes/ADRs: record important decisions when they affect
    long-term structure.

Do not duplicate large amounts of API documentation in multiple places.
Link to the canonical `api.md`.

------------------------------------------------------------------------

## 24. Observability and Health

Provide operational visibility without exposing sensitive data.

Recommended:

-   Structured application logs.
-   Request/correlation ID.
-   Request duration and status logging.
-   `/health` endpoint for process health.
-   `/ready` endpoint for readiness, including critical dependency
    checks where appropriate.
-   Safe exception logging.
-   Error monitoring such as Sentry if approved.
-   Metrics only when there is a concrete operational need.

Health endpoints must not expose secrets, environment dumps, database
credentials, or detailed internal infrastructure.

------------------------------------------------------------------------

## 25. Performance and Scalability

Build for correctness first and avoid premature infrastructure.

-   Use database indexes based on query patterns.
-   Paginate screen listing endpoints.
-   Set sensible request size and query limits.
-   Use connection pooling appropriately.
-   Avoid loading unbounded audit history.
-   Avoid N+1 database access.
-   Use asynchronous I/O where it provides a real benefit and keep
    async/sync database usage consistent.
-   Keep heartbeat writes efficient.
-   Consider write volume and status-query strategy before introducing
    scheduled bulk updates.
-   Do not add caching until measured or demonstrated need exists.

------------------------------------------------------------------------

## 26. Definition of Done

A task is complete only when all applicable items are satisfied.

### Implementation

-   [ ] Requirement is within approved MVP scope.
-   [ ] Clean Architecture boundaries are respected.
-   [ ] Business rules are implemented in the correct layer.
-   [ ] Inputs are validated.
-   [ ] Authentication and authorization are enforced where required.
-   [ ] Errors use stable system error codes and appropriate HTTP status
    codes.
-   [ ] Database changes include reviewed Alembic migrations.
-   [ ] No secrets or sensitive values are committed.

### Tests

-   [ ] Every affected use case has unit tests.
-   [ ] Every affected domain rule has unit tests.
-   [ ] External-service adapters have unit tests.
-   [ ] Every affected repository has integration tests.
-   [ ] Every affected API endpoint has integration tests.
-   [ ] Security and failure paths are tested.
-   [ ] Relevant tests pass.

### Documentation and tooling

-   [ ] `api.md` is updated for every API addition/change.
-   [ ] `.env.example` is updated if configuration changes.
-   [ ] README/operational docs are updated if setup or commands change.
-   [ ] Formatting and linting pass.
-   [ ] Pre-commit checks pass.
-   [ ] CI checks are updated if required.

### Delivery report

-   [ ] Summarise files and behaviour changed.
-   [ ] List commands and tests executed.
-   [ ] State any unverified behaviour or remaining work.
-   [ ] Mention required migration/deployment steps.

------------------------------------------------------------------------

## 27. Non-negotiable Agent Checklist

Before marking any backend task complete, verify these rules:

1.  Follow Clean Architecture: Drivers, Domain, Application,
    Adapters/Infrastructure, and Tests.
2.  Keep dependencies pointing inward.
3.  Put expected application exceptions in Application; keep HTTP
    translation in Drivers.
4.  Return stable system error codes alongside HTTP status codes.
5.  Write unit tests for every use case.
6.  Unit-test external-service adapters and their failure handling.
7.  Write integration tests for every repository implementation.
8.  Write integration tests for every API endpoint.
9.  Mirror the source package structure inside both `tests/unit` and
    `tests/integration`.
10. Use pytest.
11. Use PostgreSQL for repository integration tests; use Testcontainers
    or a dedicated Docker Compose/CI database.
12. Update `api.md` in the same change whenever an API changes.
13. Use Docker and Docker Compose for reproducible local development.
14. Use `uv` and commit `uv.lock`.
15. Use pre-commit and enforce checks in CI/CD.
16. Do not manage feature branches unless explicitly instructed.
17. Do not expose secrets, tokens, credentials or internal exception
    details.
18. Do not implement out-of-scope Adveno platform features without
    approval.
19. Do not claim tests or checks passed unless they were executed.
20. Prefer clear, maintainable, tested code over unnecessary abstraction
    or premature infrastructure.

**When in doubt:** preserve the existing architecture, inspect before
editing, ask about security- or contract-sensitive ambiguity, and
deliver implementation, tests, and documentation together.
