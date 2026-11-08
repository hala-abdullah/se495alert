# Backend Structure — PSU Alerts & Notifications

*Phase 2 companion to [architecture.md](architecture.md) and
[data-model-and-api.md](data-model-and-api.md). Describes the file-level
layout and the layering rules; it does not add entities or endpoints.*

See [backend-unit-inventory.md](backend-unit-inventory.md) for the implemented
units, their public surfaces, and test coverage.

## Layout

```text
psu-alerts/
├── manage.py
├── requirements.txt
├── scripts/run_demo                # start Django + print flutter run command
├── psu_alerts/                     # project shell
│   ├── settings.py                 # local-first config
│   ├── urls.py                     # /api/... and /admin/ (dev tool only)
│   ├── config_guard.py             # NFR-13/NFR-22 fail-fast checks
│   └── wsgi.py / asgi.py
├── core/                           # shared plumbing + demo lifecycle
│   ├── exceptions.py               # DomainError → HTTP mapping
│   ├── permissions.py              # coarse role gates
│   ├── pagination.py
│   ├── management/commands/        # seed_demo, reset_demo, check_nfr_guards
│   └── tests/                      # NFRs, deployment boundary, concurrency
├── accounts/                       # Profile, login/logout, role resolution
├── directory/                      # Department, Building, Group
├── courses/                        # Course, Section, Enrollment, FacultyAssignment
├── alerts/                         # alert domain (largest app)
│   ├── models.py                   # Alert, AlertRecipient, DeliveryRecord,
│   │                               # Acknowledgment, Category, Comment,
│   │                               # preferences, SimulatedOutboxMessage
│   ├── services/                   # the only place alert state changes
│   │   ├── compose.py              # send_alert(actor, payload)
│   │   ├── audience.py             # selector → recipient snapshot
│   │   ├── authorization.py        # role + scope + course/severity rules
│   │   ├── priority.py             # is_urgent, priority_source, ordering
│   │   ├── delivery/               # base adapter, dispatcher, email/sms/push
│   │   ├── acknowledgment.py
│   │   ├── comments.py
│   │   ├── preferences.py
│   │   └── reporting.py
│   ├── api/                        # serializers, views, permissions, filters, urls
│   ├── management/commands/send_due_reminders.py
│   └── tests/                      # one file per US group
└── audit/                          # AuditLogEntry, writer, export, comms_admin view
```

## Layering rule

```text
request → view → serializer → service → model
                    │           │
                    │           └── audit.writer.log(...)
                    └── DomainError → 400/403/409 via exception handler
```

- **Views** authenticate, apply the coarse role gate, validate input, call one
  service function, and serialize the result. No business logic.
- **Services** own authorization, audience resolution, severity/faculty
  boundaries, snapshotting, priority, delivery, acknowledgment, moderation.
  `send_alert()` is the single choke-point (NFR-1).
- **Models** own invariants only: constraints, enums, uniqueness, indexes,
  simple `clean()` rules. No cross-app workflows.
- **Adapters** implement
  `ChannelAdapter.send(alert, recipient, payload) -> DeliveryResult`; the
  dispatcher imports no real gateway (NFR-2, NFR-15).
- **Audit is written by services**, never by views. Rejections get a
  `REQUEST_DENIED` entry so AC-3.8 is structural.
- **Cross-app access is narrow:** `alerts` reads directory/course data through
  their services; `courses` asks `alerts.services.audience` to snapshot and
  never writes alert tables.

## Conventions

| Topic | Choice |
|---|---|
| API prefix | `/api/`; resource names as in the contract doc |
| Auth | DRF token auth; single `Authorization` header |
| Errors | One exception handler → `{"detail": ..., "fields": {...}}` |
| Transactions | `transaction.atomic()` around alert + snapshot + delivery rows |
| Settings | One `settings.py`; `config_guard` runs at startup |
| Time | Store UTC; locale formatting happens on the client |
| Enums | `TextChoices`; severity/category lists are config-driven |
| Tests | Per-app folders + `core/tests` for cross-cutting NFRs; authorization tests hit the API, not service internals |

Deliberately **not** added yet: a settings package, Celery, Docker, API
versioning, repository/use-case ceremony, or a shared `BaseModel`. Each adds
files without buying anything at prototype scale.
