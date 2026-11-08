# Security, Privacy, and Accessibility Considerations

*Phase 2 deliverable (T2.5), revision 2026-11-02. These are design-time
positions for the prototype; PSU's own security, privacy, and accessibility
reviews remain required before any real use (NFR-6).*

## Security

| Concern | Position for the prototype | Enforced by |
|---------|---------------------------|-------------|
| Authorization | Every role, audience, and course/section boundary enforced **server-side** in the alerts service; the Flutter client is untrusted. Officers send only within granted scopes; faculty only to assigned courses/sections; every rejected request (send or not) is refused with 401/403 and audited (AC-3.2, AC-3.6, AC-3.8, AC-14.1, NFR-1) | Independent API-level 403 tests written against the contract, not implementation internals (R4) |
| Authentication | DRF token auth; synthetic PSU-shaped demo accounts; passwords hashed by Django; no real PSU credentials or SSO in v1 (NFR-21) | `accounts` tests; seed review; handoff note |
| Session handling | Logout invalidates the token; failed logins audited (`LOGIN_FAILED`); generic 401 message does not reveal which field failed (AC-9.1–9.3) | Auth tests |
| Transport | Localhost HTTP is acceptable **only** in the local demo. NFR-22 requires HTTPS for any non-local host; the settings guard refuses to start otherwise | Settings-guard test; README handoff checklist |
| Encryption at rest | SQLite has no built-in encryption. The demo stores synthetic data only; any non-local deployment must use an encrypted volume or SQLCipher. We do **not** claim the demo DB is encrypted (NFR-22) | Handoff checklist; settings guard requires an explicit acknowledgement flag outside local mode |
| Secrets | Dev `SECRET_KEY` and `DEBUG=True` are acceptable **only** under the local-deployment boundary (ADR-001). Any move off localhost must load secrets from environment and disable DEBUG | Pre-demo settings review; secret scan (NFR-18) |
| Abuse / spam | No rate limiting or dedupe in v1 — documented known gap (A-12, R2). Comments are recipient-only, plain text, length-limited, and moderator-removable; this reduces but does not eliminate abuse (R14) | Risk register; Phase 5 impact analysis |
| Input | DRF serializers validate all fields; severity/category restricted to configured lists (AC-1.3, AC-11.1); comment bodies are plain text, escaped, 1–500 chars (AC-17.2); no `eval`/dynamic include patterns | Serializer/comment tests; code review |
| Comments | Posting requires recipient status; reading restricted to recipients/sender/comms_admin; removal is soft delete with actor + timestamp; moderation audited (US-17) | Comment authorization + moderation tests |
| Dependencies | Pinned Python versions in `requirements.txt`; Flutter/Dart dependencies pinned in `pubspec.yaml`; permissive licenses only (NFR-17) | Setup rehearsal; license inventory |
| Deployment guard | NFR-13/NFR-22 guard fails fast on DEBUG with non-local hosts, a network-capable email backend, missing HTTPS/encryption acknowledgement outside local mode | `check_nfr_guards` test |

## Privacy

| Concern | Position for the prototype | Enforced by |
|---------|---------------------------|-------------|
| Contact data | **Synthetic only, ever.** Emails use `@example.edu`-style fakes; phones are fake or null. No real PSU directory data may enter the repo, seed command, logs, or demos (NFR-1, A-13) | Seed-data review; test asserting synthetic domain patterns; pre-demo screenshot checklist |
| Course/enrollment data | Synthetic courses, sections and enrollments only. No real student records or enrollment exports (C-3, C-5, R13) | Seed review; no import path from real sources in v1 |
| Logs | Log lines and audit entries reference **user IDs and counts**, never email addresses or phone numbers (NFR-3) | Log-capture test asserting absence of address/phone patterns |
| Audit content | AuditLogEntry stores actor ID, action, object refs, and JSON detail of IDs/counts only | Serializer on the audit writer; review |
| Comments | Stored as authored; visible only to the alert audience/sender/admin; soft-deleted content retained for audit. Comment text may contain personal data volunteered by the author — no contact data is required or requested | Access-control tests; moderation policy |
| Retention | Prototype retains everything (alerts, deliveries, acks, comments) indefinitely in the local SQLite file — acceptable because data is synthetic; a real deployment needs a retention policy (flagged for PSU) | README limitations |
| Demo hygiene | Demo script and screenshots use synthetic accounts; no PSU confidential data is sent to the AI provider at any point (C-5) | AI-use log discipline; team review |

## Accessibility

| Concern | Position for the prototype | Enforced by |
|---------|---------------------------|-------------|
| UI foundation | Flutter widgets with semantic labels, logical focus order, and touch targets ≥44 px at 360–430 logical px widths (NFR-14) — no hover-only or icon-only controls for critical actions | Widget tests; manual emulator pass |
| Acknowledgment control | The ack action is a labelled button (not an icon-only control); state change is announced via semantics and visible text (AC-5.x, AC-13.2) | Widget tests; manual screen-reader pass |
| Color/severity | Severity is never conveyed by colour alone — each alert shows a severity text label and, for urgent/critical, an explicit banner (NFR-20) | UI review checklist; golden tests |
| Bilingual / RTL | Full EN/AR with `Directionality.rtl`, mirrored navigation and rows, no half-mirrored screens; meaning still carried by text/icon, not direction (NFR-19/NFR-20) | RTL widget tests; AR emulator pass |
| Contrast & text scaling | Default Material themes kept to accessible contrast; text scaling tested to 130%; no fixed-height text containers | Flutter widget tests at scaled text |
| Boundary | Full WCAG conformance is **not** claimed; the prototype records accessibility as a PSU-review item (NFR-6). Our obligation is to not knowingly ship barriers and to document the gap honestly | README limitations; this document |

## Summary for evaluators

The prototype's security story is *correct boundaries, audited denials, and
synthetic data* — not production hardening. What PSU must review before real
use: identity integration (SSO), secrets/HTTPS, encrypted storage, rate
limiting, retention, comment moderation policy, gateway-level delivery
security, concurrency beyond SQLite, and a formal accessibility audit.
