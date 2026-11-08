# Working Assumptions — PSU Alerts & Notifications

*Phase 1 deliverable. Each assumption is either **working** (we build against
it and flag it in the AI-use log) or **open** (pending a stakeholder answer —
see [stakeholder-questions.md](stakeholder-questions.md)). Revision 2026-11-02
adds the course/faculty/comment/priority assumptions required by the supplied
Requirements and Design documents.*

## Technology

| ID | Assumption | Status | Consequence if wrong |
|----|-----------|--------|----------------------|
| A-1 | Stack is **Python 3.14 + Django 5.1 + Django REST Framework + SQLite** for the backend, with a **Flutter** mobile client (Design Doc §1–2) | Working (revised 2026-11-02 from server-rendered Django templates) | Requirements are written against API behavior, so a client swap is contained; Flutter adds a second toolchain (R12) |
| A-2 | Local single-machine deployment is enough; no Docker/production WSGI needed for the prototype | Working (brief states local is sufficient) | Minimal: add container config later |
| A-3 | Simple token/session login with synthetic **PSU-shaped** demo accounts is acceptable; no real PSU SSO | Working (brief: authentication optional; supplied docs say "PSU account") | A real SSO adapter is the handoff seam; no data-model change beyond the auth adapter |
| A-22 | Flutter runs against the Django API on localhost/emulator; a single `scripts/run_demo` wrapper starts the backend and documents `flutter run` | Working | If a device build is needed, add platform run instructions — no architectural change |

## Domain

| ID | Assumption | Status | Consequence if wrong |
|----|-----------|--------|----------------------|
| A-4 | Three severity levels (CRITICAL / ADVISORY / INFORMATIONAL) map to Design Doc high/medium/low | Working (was OPEN-Q4; supplied docs confirm the three bands implicitly) | Tests parameterize over the configured list; a 2- or 4-level answer is a config change |
| A-5 | Acknowledgment required for CRITICAL only | Working (supplied docs' AC-5.1 confirms) | One conditional flag in the ack endpoint |
| A-6 | Alerts expire after explicit end time or 24 h default, then remain in history | Working (supplied docs' AC-6.1 confirms) | History queries already filter by lifecycle state |
| A-7 | One audience selector per alert in v1 (no AND/OR combinations) | Working — keeps targeting testable | Combined selectors can be a later increment |
| A-8 | Recipient list is snapshotted at send time | Working | If PSU wants live re-resolution, delivery model changes materially |
| A-9 | No edit/cancel after send; corrections are follow-up alerts | Working (supplied docs' AC-1.4 confirms) | If edit is required, audit design needs versioning |
| A-10 | Invented synthetic org taxonomy: ~4 colleges/departments, ~6 buildings, ~60 people | Working | Seed data only; low cost |
| A-12 | Deduplication / rate limiting of repeated alerts is out of scope (possible Phase 5 change request) | Working (known gap) | Planned change-request exercise, not an accident |
| A-19 | **Category is a second axis to severity**, managed by comms_admin with seeded defaults (CLOSURE/SAFETY/EVENT/SCHEDULE/OTHER + EXAM/DEADLINE); templates remain stretch (US-11) | Working; vocabulary open to PSU revision | Vocabulary change is seed/data only |
| A-22 | **Courses, sections and enrollments are synthetic.** Faculty grants are explicit per course/section; the data model can be replaced by a PSU SIS import at handoff | Working (R13) | Real enrollment integration is a handoff adapter, not a v1 feature |
| A-23 | **Faculty severity boundary:** faculty send ADVISORY/INFORMATIONAL to their own courses and may set `is_urgent`; CRITICAL and campus-wide sends stay with officers/comms_admin. Resolves the Design Doc §3.2 vs Requirements Doc conflict | Working (Q14) | If PSU wants faculty CRITICAL, relax the service rule; audit and ack already support it |
| A-24 | **Urgent is a priority override, not a severity.** It affects ordering, mute bypass and sound/vibration payload, but does not change severity or ack requirements | Working | If PSU wants a fourth severity, that is a config/data change with reporting impact |
| A-25 | **Deadline reminders are dispatched by a local management command** (`send_due_reminders`), not an external scheduler | Working | A real scheduler is a deployment/handoff concern; command semantics stay |
| A-26 | **Comments are in scope** with recipient-only posting, plain text, and comms_admin soft-delete moderation (US-17) | Working (supplied docs UC-05 + §5 ER model) | If comments are dropped, remove US-17 and the Comment entity; no other feature depends on it |
| A-27 | **Event opt-out is allowed; mandatory categories bypass it.** EVENT/OTHER can be disabled; CLOSURE/SAFETY/EXAM/DEADLINE/urgent/schedule-change cannot | Working (supplied docs' event + exam/urgent criteria) | If PSU wants all categories mutable, the bypass table changes; tests make the policy explicit |
| A-28 | **Exam/deadline structured fields are required at send** for those categories; schedule-change requires at least one old/new pair | Working | Relaxing to optional is a serializer change; history display already tolerates nulls |

## Data & privacy

| ID | Assumption | Status | Consequence if wrong |
|----|-----------|--------|----------------------|
| A-13 | All directory and contact data is generated fake data; emails use `example.edu`-style domains | Working (brief mandates it) | None — this is a hard constraint, not a preference |
| A-14 | Seed data is created by repeatable management commands, not committed spreadsheets | Working | Easier reset and review |
| A-17 | **Read ≠ acknowledgment.** Read is a view receipt on any alert; ack is an explicit action on CRITICAL only; ack implies read (US-13, AC-13.2) | Working (2026-10-20) — hardens demo-language risk R10 into the model | If PSU wants a single "seen" concept, ack/read collapse into one flag |
| A-18 | **Portal is an always-on channel.** Device preferences modulate only EMAIL/SMS/PUSH; the in-app announcements/history view always shows everything sent to the user | Working (2026-10-20) — makes AC-12.4 coherent | If PSU wants portal visibility controllable too, the preference model gains a fourth channel |
| A-20 | **No machine translation of alert content.** Title/body are authored by the sender in their chosen language and stored as entered; the interface around them is bilingual (NFR-19) | Working (2026-10-20) — rejected alternatives in AI-14: runtime translation would violate C-1/C-2 and a mistranslated CRITICAL message is a safety hazard | If PSU requires dual-language alert text, use paired fields (`title_en`/`title_ar`) filled manually by the sender — a contained schema addition |
| A-21 | **Bilingual vocabulary labels.** Seeded categories and severity labels carry EN and AR names; admin-created categories may be single-language and display as entered | Working | Fallback to entered text keeps single-language data from breaking NFR-19 |
| A-29 | **Encryption is a deployment boundary, not a demo claim.** Localhost + synthetic data is the prototype; non-local deployments require HTTPS and encrypted storage (NFR-22) | Working (supplied docs ask for encryption; SQLite cannot provide it natively) | If PSU requires at-rest encryption in the demo, add SQLCipher as a dependency and a migration step |
| A-30 | **Concurrency target is modest** (50 concurrent reads / 5 sends at seed scale) with SQLite WAL; PostgreSQL is the handoff for exam-period scale | Working (supplied docs' "multiple users at the same time") | Higher targets require PostgreSQL and a load test; no API change |

## Process

| ID | Assumption | Status | Consequence if wrong |
|----|-----------|--------|----------------------|
| A-15 | Stakeholder answers arrive through the instructor; we build against recommendations meanwhile | Working (brief: consolidate via instructor) | Adjustments are localized per the "consequence if wrong" notes above |
| A-16 | One primary developer working with an AI agent; team-review rituals from the brief adapted accordingly | Working | Task plan slack absorbs review time |
