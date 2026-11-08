# Reconciliation — Supplied Documents (2026-11-02)

*Why this document exists: the project was already in Phase 2 when two newer
inputs arrived. Copying either document verbatim would have broken the course
constraints (C-1…C-6) or contradicted the other document. This note records
what changed, what was rejected, and where the boundary sits, so the decision
is auditable rather than hidden in a rewrite.*

## Inputs

| Source | What it supplies | Authority |
|--------|------------------|-----------|
| `Requirments Doc.md` | US-1…US-13 acceptance criteria, roles, NFR-1…NFR-20, constraints, additional user stories/use cases, category acceptance criteria | Authoritative for **what** the system must do |
| `Design Doc.md` | Three-tier Flutter/Django/SQLite architecture (§1–2), navigation (§3), ER model (§5), component flows (§6) | Authoritative for **architecture direction**; §4–6 contain older/aspirational text |
| `PSU_Alerts_Notifications_Project_Brief.md` | Course constraints, phases, deliverables | Hard boundary (no budget, no real gateways, synthetic data, PSU review) |
| Existing project docs (v1/v2) | Prior elicitation, NFR backlog, architecture, ADRs | Revised where inconsistent; history preserved in revision lines |

## Decisions

### D1 — Flutter is the presentation layer (replaces server-rendered Django templates)

The supplied Design Doc is explicit: a Flutter mobile app talks to a Django
REST/JSON API; "admin screens inside the Flutter app". The previous ADR-001
choice of Django templates is therefore superseded. Consequences:

- `docs/design/architecture.md`, `data-model-and-api.md`, `ADR-001` and the
  README now describe the Flutter client.
- The Django admin site remains a **developer** tool only; it is not the
  comms_admin UI and is not part of the mobile-only product surface.
- Bilingual/RTL work moves to Flutter (`intl`/ARB + `Directionality`) instead
  of Django gettext templates, while API vocabulary stays bilingual.

### D2 — Simulated delivery stays; Firebase/APNs and PSU SSO are handoff items

`Design Doc.md` §6 names Firebase Cloud Messaging + APNs, a PSU SSO/OAuth
authentication service, PostgreSQL/MySQL, and an optional web admin dashboard.
`Design Doc.md` §1–2 simultaneously says delivery is simulated in-backend,
accounts are local/synthetic, SQLite is used, and the UI is mobile-only. The
second set is consistent with C-1…C-5; the first set is not. Resolution:

- v1 uses the `ChannelAdapter` seam (console email, local SMS/push outbox).
- v1 login uses synthetic PSU-shaped accounts; a real SSO adapter is the
  documented handoff seam (NFR-21).
- SQLite stays; PostgreSQL is a handoff note for write concurrency.
- No web dashboard is built (NFR-14).

### D3 — Faculty course alerts are added, with a severity boundary

`Requirments Doc.md` adds Faculty course/section stories and comments;
`Design Doc.md` adds a Course/Enrollment/Comment data model. Both are adopted.
But the documents disagree on Faculty severity: Design Doc §3.2 allows Faculty
only medium/low, while the Requirements Doc wants Faculty to mark alerts
"Urgent". Resolution (US-14/US-16):

- Faculty may send `ADVISORY`/`INFORMATIONAL` to assigned courses/sections.
- Faculty may set `is_urgent` on those alerts (higher priority, distinct
  sound/vibration, bypasses mutes).
- `CRITICAL` and campus-wide/department-wide sends remain with Alert Officers
  and Comms Admin. This preserves the safety escalation path and the Design
  Doc's "faculty medium to low" rule at the severity level.

### D4 — "Push within 1 minute" is a simulated-delivery SLA

C-2 forbids a real gateway. The measurable version is NFR-23: all simulated
delivery rows terminal and visible within 60 s of the send timestamp. The
synchronous simulator completes far faster; the test measures elapsed time so
the requirement is still demonstrated. Real push timing is a handoff metric.

### D5 — "PSU account" and "encrypted at rest" are boundaries, not false claims

- Login uses PSU-shaped synthetic accounts (`student ID`/username, password
  hash), no real credentials or directory data. NFR-21.
- SQLite has no built-in at-rest encryption. The prototype stores synthetic
  data only; NFR-22 requires HTTPS and an encrypted volume/SQLCipher for any
  non-localhost deployment, enforced by a startup guard and documented in the
  security note. We do **not** claim the demo database is encrypted.

### D6 — Comments are in scope with moderation

`Requirments Doc.md` UC-05 plus the comment acceptance criteria and
`Design Doc.md` §5 (`Alert ||--o{ Comment`) make comments part of the product,
not a stretch item. Adopted as US-17 with soft-delete moderation by
comms_admin, plain-text bodies, recipient-only posting and audit logging.

### D7 — Category opt-outs are allowed, with mandatory categories

The Requirements Doc asks for event opt-in/opt-out but also says exam alerts
must arrive even when other categories are muted, and urgent alerts cannot be
muted. US-12/US-16 implement:

- Opt-out allowed for `EVENT` and `OTHER`.
- `CLOSURE`, `SAFETY`, `EXAM`, `DEADLINE`, schedule-change, urgent and
  `CRITICAL` bypass category mutes.
- Channel preferences still apply to non-mandatory alerts; mandatory alerts
  force the simulated push record and portal row.

### D8 — NFR numbering compacted

The live NFR table is now NFR-1…NFR-24, matching the supplied document's
NFR-1…NFR-20 and adding NFR-21 (auth boundary), NFR-22 (encryption boundary),
NFR-23 (one-minute delivery) and NFR-24 (concurrency). Old references in the
AI-use log are historical and keep their original numbers; live docs use the
new numbers. `NFR-20` no longer cross-references a non-existent "NFR-23".

### D9 — Three role families: Student, Faculty, Admin

Stakeholder wording describes three roles — **admin, faculty, student** — while
the supplied Requirements Document also distinguishes Alert Officer from
Communications Admin, and lists PSU IT as a reviewer. Resolution:

- The **role families** are Student (`student`), Faculty (`faculty`) and Admin
  (`officer` + `comms_admin`). The backend derives each user's permitted
  parameters from the family plus stored grants.
- The finer Admin split is retained because it is a real security boundary:
  an Alert Officer sends only within granted scopes, a Communications Admin
  sends anywhere and manages categories, grants, comments and reports.
- `psu_it` remains a review-only role, not a runtime delivery role, and the
  development team is not an application login role.

This keeps the stakeholder's three-role mental model while preserving the
least-privilege distinction the requirements document requires.

## What was deliberately not changed

- Three-tier architecture and the single service-layer choke-point.
- Transactional send, snapshot-at-send, append-only audit, terminal delivery
  states.
- No edit/cancel after send.
- Synthetic data only; no real contact details anywhere.
- Mobile-only 360–430 px, ≥44 px targets, EN/AR + RTL.

## Residual risks introduced by the new scope

| Risk | Mitigation |
|------|------------|
| Flutter adds a second toolchain and a client/server contract to keep in sync | Recorded as R12; API contract remains the single source; Flutter tests run against the contract |
| Course/enrollment data is synthetic and may not match PSU structures | Recorded as R13; data model keeps Course/Section/Enrollment replaceable; no real records |
| Comments create abuse/moderation surface | US-17 limits posting to recipients, plain text only, soft delete + audit; rate limiting remains a known gap |
| Encryption/concurrency claims could be over-read as production readiness | NFR-22/NFR-24 and the security note state the local boundary and the handoff work explicitly |
| Faculty/urgent severity boundary may be revisited by PSU | Q14 records the decision; severity is config-driven, so a policy change is a small rules change |

## Open questions carried forward

See [stakeholder-questions.md](stakeholder-questions.md): Q13 (comment
moderation policy), Q14 (faculty urgent vs critical), Q15 (real PSU SSO
timeline), Q16 (whether 60 s is the intended push SLA), Q17 (course/enrollment
data source at handoff).
