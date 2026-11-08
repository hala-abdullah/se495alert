# PSU Alerts & Notifications — Prototype

Campus-wide urgent alerting prototype for PSU University Communications,
built as the course project for *AI in Software Engineering*. Students,
faculty, alert officers and Communications admins use a **Flutter mobile app**
to receive and send targeted alerts; a **Django REST backend** enforces every
role, audience and course boundary, simulates delivery locally, and keeps an
auditable record of critical acknowledgments.

> **Prototype only.** Synthetic data, simulated channels, local deployment.
> PSU security, privacy, accessibility, and operational reviews are required
> before any real use (NFR-6). No real student, faculty, or staff contact
> information may ever be added to this repository (NFR-3, C-3/C-5).

## Status

| Phase | State |
|-------|-------|
| 1 — Requirements & planning | **Complete** (2026-10-19; revised 2026-11-02) |
| 2 — Architecture & design | **Complete** (2026-10-19; revised 2026-11-02) |
| 3 — Implementation | Not started (Weeks 3–7, see [task plan](docs/task-plan.md)) |
| 4 — Testing & verification | Not started (Weeks 6–7) |
| 5 — Change request | Not started (assigned after Milestone 1) |

Milestone 1 checklist: stakeholder questions ✔ · requirements + acceptance
criteria (US-1…US-17) ✔ · assumptions/risks/task plan ✔ · architecture diagram ✔ ·
data model + API contract ✔ · screen navigation ✔ · ADR-001 + ADR-002 ✔ ·
security/privacy/accessibility note ✔ · supplied-document reconciliation ✔ ·
AI-use evidence log (M1 entries) ✔ — final M1 review (T2.7) remains before
submission.

**2026-11-02 revision:** the project was reconciled against the supplied
`Requirments Doc.md` and `Design Doc.md`. The presentation layer is now a
Flutter mobile app (replacing the earlier server-rendered Django templates),
course/section alerts, exam and deadline reminders, urgent priority overrides
and moderated comments are in scope, and NFRs were compacted to NFR-1…NFR-24.
What changed, what was rejected, and why: [reconciliation note](docs/reconciliation-2026-11-02.md).

## Stack

Three-tier: **Flutter client → Django application layer → SQLite database**.

- **Mobile client:** Flutter/Dart, mobile-phone-only (360–430 logical px,
  single column, touch targets ≥44 px), bilingual English/Arabic with full RTL.
- **Backend:** Python 3.14 · Django 5.1 · Django REST Framework 3.17. Owns
  authentication, role-based authorization (Student / Faculty / Admin),
  alert creation, audience/group selection and acknowledgment tracking.
- **Database:** SQLite (WAL mode) with synthetic records only.
- **Delivery:** simulated in the backend — email to the Django console
  backend, SMS/push to a local outbox table. No paid service and no outbound
  network call exists in the send path (NFR-2).
- **Admin UI:** screens inside the Flutter app. The Django admin site is a
  developer tool only, not a product surface.

Every unauthorized request is rejected by the backend with HTTP 401/403 and
written to the audit log with actor, action, requested object and timestamp
(AC-3.8) — rejection is evidence, not a silent failure.

## Setup

### Backend

```bash
cd backend
python -m venv .venv          # on Windows, if `python` is the Store stub:
                              #   & "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -m venv .venv
.venv\Scripts\activate        # Unix: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py test         # 84 tests: auth, role/scope authorization, audit, security regressions
```

Optionally: `python manage.py createsuperuser`, then
`python manage.py runserver` and open `/admin/` or `/api/health/`.

A runnable faculty authorization showcase is available now:

```bash
python manage.py demo_faculty_send    # one allowed send + three denials, with audit rows
```

Phase 3 adds the remaining demo data and reset commands:

```bash
python manage.py seed_demo            # synthetic users, courses, enrollments, categories
python manage.py reset_demo           # restore a known demo state (NFR-12)
python manage.py send_due_reminders   # dispatch due deadline reminders (AC-15.4)
```

### Mobile app

Requires the free Flutter SDK plus an Android/iOS emulator or device. Added in
T3.1 (Week 3–4):

```bash
cd ../frontend
flutter pub get
flutter test                          # widget/layout tests, no device needed
flutter run                           # with the Django server running on localhost
```

The app talks to `http://localhost:8000/api/` in the local demo. Non-local
hosts are refused by the settings guard unless HTTPS and encrypted storage are
acknowledged (NFR-22).

## Repository layout

```
docs/                          Phase 1–2 deliverables (the engineering evidence)
  stakeholder-questions.md     Consolidated questions for PSU (via instructor)
  requirements.md              US-1…US-17 + testable acceptance criteria, NFR-1…NFR-24
  reconciliation-2026-11-02.md What changed against the supplied documents, and why
  assumptions.md               Working/open assumptions with consequences
  risks.md                     Risk register (R1…R16)
  task-plan.md                 Task breakdown traced to requirements
  ai-use-evidence-log.md       What the AI contributed, kept, and got wrong
  design/                      Phase 2 package
    architecture.md            Three-tier diagram + send/reminder flows
    data-model-and-api.md      Entities, fields, endpoint contract, commands
    screen-navigation.md       Role-based Flutter navigation map
    adr/ADR-001-*.md           Stack, deployment boundary, UI approach (Flutter)
    adr/ADR-002-*.md           Delivery simulation (adapters, 60 s SLA, mute bypass)
    security-privacy-accessibility.md
psu_alerts/                    Django project (settings, root URLs, guards)
accounts/                      Login, profiles, sender grants          (Phase 3)
directory/                     Departments, buildings, groups          (Phase 3)
courses/                       Courses, sections, enrollments          (Phase 3)
alerts/                        Alerts, delivery, ack, comments, prefs  (Phase 3)
audit/                         Append-only audit log + export          (Phase 3)
../frontend/                   Flutter app (separate folder)           (Phase 3)
```

## Scope boundary (first release)

In scope: PSU-shaped synthetic login · server-side role/audience/course
authorization · composing alerts with severity **and** category · campus,
role, department, building, group, course and section targeting · faculty
course alerts · exam announcements and deadline reminders · schedule changes
and the urgent priority override · simulated multi-channel delivery with
status · device and category preferences · read status · critical
acknowledgment · history and filtering · moderated comments · administrative
and audit reporting · bilingual EN/AR with RTL.

Out of scope (documented, not silently dropped): real SMS/push/email gateways
and Firebase/APNs · real PSU SSO/OAuth and real directory or enrollment data ·
machine translation of alert content · approval workflows and duplicate
suppression · a web admin dashboard · PostgreSQL/MySQL, production HTTPS and
encrypted storage (handoff boundary, NFR-22) · editing or cancelling an alert
after send.

See [requirements.md](docs/requirements.md) for the authoritative scope and
the conflict table, and [reconciliation-2026-11-02.md](docs/reconciliation-2026-11-02.md)
for the reasoning.

## License inventory

All runtime dependencies must carry a permissive license (BSD/MIT/Apache-2.0)
— NFR-17. This table is completed as dependencies are pinned in Phase 3.

| Component | Version | License | Status |
|-----------|---------|---------|--------|
| Python | 3.14 | PSF License | ✔ |
| Django | 5.1.15 | BSD-3-Clause | ✔ |
| Django REST Framework | 3.17.2 | BSD-3-Clause | ✔ |
| Flutter / Dart SDK | TBD (T3.1) | BSD-3-Clause | pending |
| Flutter app packages | TBD (T3.1) | verify each | pending |

## Limitations and handoff (PSU review required)

- Delivery is **simulated**; no message leaves the machine. Real gateway
  timing is a deployment metric, not a prototype claim (NFR-23).
- The demo SQLite file is **not** encrypted at rest. Any non-local deployment
  requires HTTPS plus an encrypted volume or SQLCipher (NFR-22).
- Authentication is synthetic and PSU-shaped; a real SSO/OAuth adapter is a
  handoff seam (NFR-21).
- Concurrency is sized for prototype scale (≈50 reads / 5 sends, NFR-24);
  PostgreSQL is the handoff for exam-period load.
- "Acknowledged" is an explicit action, never the same as "read" (AC-13.2).
- No rate limiting or duplicate suppression; comments are moderated but not
  spam-filtered.
- Full WCAG conformance is not claimed; accessibility is a PSU review item.

Before real use, PSU must review security, privacy, accessibility, identity
integration, retention, moderation policy, gateway integration and deployment.
