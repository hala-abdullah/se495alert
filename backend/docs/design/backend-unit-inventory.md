# Backend Unit Inventory — PSU Alerts & Notifications

*Companion to [backend-structure.md](backend-structure.md). Snapshot: 2026-11-08.
Shows what exists today, what each unit owns, and which tests cover it. Planned
units from the Phase 2 structure are listed separately so the gap is explicit.*

## What counts as a unit

A **backend unit** is a module-level thing with one responsibility and a
public surface: a model class, a permission class, a service function, a view,
or a management command. Private helpers (`_authorize`, `_target_ids`, …) are
implementation details of their unit and are tested through the public
function.

Unit tests live in app folders; the cross-cutting security regressions live in
`alerts/test_security.py` and `accounts/tests/test_security.py`.

---

## 1. Project shell

| Unit | Public surface | Responsibility | Tests |
|---|---|---|---|
| `psu_alerts/settings.py` | settings module | App registry, DRF defaults (token auth, `IsAuthenticated`, exception handler), local SQLite, console email | `alerts/tests.py` (email never leaves process); auth tests rely on the auth defaults |
| `psu_alerts/urls.py` | `health()`, `urlpatterns` | Routes `/admin/`, `/api/health/` (GET only), includes `accounts.urls` | `alerts/tests.py::test_health_endpoint_returns_ok`; `accounts/tests/test_security.py` (anonymous, minimal, 405 on non-GET) |
| `manage.py` | `main()` | Standard Django entry point | exercised by every test run |

`wsgi.py` / `asgi.py` are deployment stubs with no behaviour of their own.

## 2. Cross-cutting plumbing

| Unit | Public surface | Responsibility | Tests |
|---|---|---|---|
| `core/exceptions.py` | `custom_exception_handler` | Normalise DRF errors to `{"detail", "fields"}`; audit every 401/403 as `REQUEST_DENIED`; never let audit failure break the response | `accounts/tests/test_auth.py` (anonymous `/me`, role gate); `accounts/tests/test_security.py` (bad token) |
| `core/permissions.py` | `IsStudent`, `IsFaculty`, `IsAdminRole`, `IsOfficer`, `IsCommsAdmin` | Coarse "may this role reach this endpoint" gates; object rules stay in the services | `RoleGateTests` covers `IsCommsAdmin` only — the other four have **no direct unit test yet** |
| `audit/models.py` | `AuditLogEntry` | Append-only event row; `save()` on an existing PK raises | `audit/tests/test_audit.py`; `alerts/test_security.py::test_append_only_admin_has_no_mutation_paths` |
| `audit/writer.py` | `log()` | Single write path; truncates labels/refs; actor -> `null` when anonymous | `audit/tests/test_audit.py`; `AuditBoundaryTests` |
| `audit/admin.py` | `AuditLogEntryAdmin` | Read-only developer view | `AuditBoundaryTests::test_append_only_admin_has_no_mutation_paths` |

## 3. Identity, authentication and roles

| Unit | Public surface | Responsibility | Tests |
|---|---|---|---|
| `accounts/models.py` | `RoleFamily`, `Profile`, `OfficerScope` | Two role axes; derived `role_family` (Admin > Faculty > Student); officer grants with check/unique constraints | `accounts/tests/test_auth.py`; `alerts/test_authorization.py`; `alerts/test_security.py` (`AuthorizationMatrixTests`, `GrantIntegrityTests`) |
| `accounts/services.py` | `get_profile`, `resolve_role_family`, `authenticate_credentials`, `build_identity` | Default-safe profile creation; credential check; role resolution; UI identity payload | `accounts/tests/test_auth.py` (identity/role cases); `test_security.py` (mass assignment) |
| `accounts/serializers.py` | `LoginSerializer`, `IdentitySerializer` | Validate login input; document identity shape | `accounts/tests/test_auth.py` (missing field, extra privileges ignored) |
| `accounts/views.py` | `LoginView`, `LogoutView`, `MeView` | Issue/revoke DRF tokens; return `build_identity`; audit login/logout | `accounts/tests/test_auth.py`; `accounts/tests/test_security.py` |
| `accounts/urls.py` | `auth/login/`, `auth/logout/`, `me/` | Route identity endpoints | via view tests |
| `accounts/admin.py` | `ProfileAdmin` | Developer view of profiles (`role_family` read-only) | no dedicated test (developer tool) |

## 4. Synthetic directory and course data

| Unit | Public surface | Responsibility | Tests |
|---|---|---|---|
| `directory/models.py` | `Department`, `Building`, `Group` | Synthetic targeting entities; `Group.members` M2M | used in authorization/audience fixtures; no standalone model tests |
| `courses/models.py` | `Course`, `Section`, `Enrollment`, `FacultyAssignment` | Course/section structure; active enrollment; whole-course vs section grant; `save()` enforces section→course match | `alerts/test_authorization.py`; `GrantIntegrityTests` (mismatch, duplicates); `AudienceSnapshotTests` (active enrollment, dedupe) |

## 5. Alerts domain (implemented subset)

| Unit | Public surface | Responsibility | Tests |
|---|---|---|---|
| `alerts/constants.py` | `Severity`, `AudienceType`, `PrioritySource` | Whitelisted vocabulary for validation | exercised through `authorize_send`; no standalone test |
| `alerts/services/authorization.py` | `SendDenied`, `SendRequest`, `authorize_send` | Single policy choke-point: role family, severity cap, faculty grants, officer scopes, comms-admin override, selector shape/type/urgency validation, denial audit | `alerts/test_authorization.py` (20); `AuthorizationMatrixTests`, `AuditBoundaryTests`, `InvalidInputTests` (7) |
| `alerts/services/audience.py` | `resolve_recipients` | Selector -> materialised recipient list using active enrollments/groups; dedupe and PK order; validates selector, target type and IDs; `[]` on any malformed input | `AudienceSnapshotTests` (8), `AudienceInputTests` (4) |
| `alerts/management/commands/demo_faculty_send.py` | `Command` | Idempotent synthetic seed + runnable allowed/denied send showcase | manual run only — **not automated** |
| `alerts/models.py`, `alerts/views.py`, `alerts/admin.py` | *(empty placeholders)* | Reserved for the alert lifecycle (T3.5) | — |

## 6. Test inventory (84 tests)

| File | Count | Focus |
|---|---:|---|
| `accounts/tests/test_auth.py` | 15 | Login, identity, logout, one role gate |
| `accounts/tests/test_security.py` | 7 | Token handling, mass assignment, password storage, health |
| `alerts/test_authorization.py` | 20 | Faculty/officer rules and denial audit |
| `alerts/test_security.py` | 38 | Matrix, revocation, audit integrity, grant constraints, audience snapshots, malformed input |
| `audit/tests/test_audit.py` | 2 | Append-only |
| `alerts/tests.py` | 2 | Health, console email |

Test classes use the fast MD5 hasher via `@override_settings`; production
settings keep Django's default PBKDF2. Full suite runs in well under a second.

---

## 7. Dependency direction

```text
views / management commands
        │
        ▼
services (authorization, audience) ──► audit.writer
        │
        ▼
models (accounts, courses, directory, audit)
        │
        ▼
SQLite (synthetic data only)
```

Rules that hold today:

- Views never contain policy; they delegate to services.
- `alerts` reads course/directory data but does not write it.
- `courses` does not import `alerts`.
- Audit writes go through `audit.writer.log`, never directly through models.
- The Flutter client is untrusted; identity payloads are hints only.

## 8. Planned units (not implemented)

From [backend-structure.md](backend-structure.md):

| Area | Planned unit | Status |
|---|---|---|
| Config | `psu_alerts/config_guard.py` (NFR-13/NFR-22) | missing |
| Shared | `core/pagination.py` | missing |
| Ops | `core/management/commands/{seed_demo,reset_demo,check_nfr_guards}` | missing |
| Cross-cutting tests | `core/tests/` (deployment boundary, concurrency) | missing |
| Alert lifecycle | `alerts/models.py`: `Alert`, `AlertRecipient`, `DeliveryRecord`, `Acknowledgment`, `Category`, `Comment`, preferences, outbox | missing |
| Send pipeline | `alerts/services/compose.py::send_alert` | missing |
| Priority | `alerts/services/priority.py` | missing |
| Delivery | `alerts/services/delivery/` adapter + dispatcher | missing |
| Recipient actions | `alerts/services/acknowledgment.py`, `comments.py`, `preferences.py` | missing |
| Reporting | `alerts/services/reporting.py` | missing |
| API | `alerts/api/` serializers, views, permissions, filters, urls | missing |
| Audit export | audit export/view for comms admin | missing |
| Demo runner | `scripts/run_demo` | missing |

## 9. Known unit-test gaps

1. `core/permissions.py`: only `IsCommsAdmin` is exercised; `IsStudent`,
   `IsFaculty`, `IsAdminRole`, `IsOfficer` need a table test (anonymous,
   wrong family, right family).
2. `alerts/management/commands/demo_faculty_send.py`: no smoke test; a broken
   seed would only be caught by running it manually.
3. `directory` and `courses` have no standalone model tests beyond the grant
   constraints exercised through alert tests.
4. `alerts/constants.py` has no test asserting the accepted values match the
   contract.
5. API-boundary tests (IDOR, generic 403 bodies, endpoint permission wiring)
   are blocked on the send/read/ack endpoints.
