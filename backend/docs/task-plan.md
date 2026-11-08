# Task Plan — PSU Alerts & Notifications

*Phase 1 deliverable. Tasks are traced to requirements (US/NFR IDs) so progress
and test coverage can be audited. Schedule follows the brief's 8-week table;
adjust freely at the weekly review.*

**Revision 2026-11-02:** the plan now reflects the supplied `Requirments Doc.md`
and `Design Doc.md` — Flutter client, courses/sections/enrollments, exam and
deadline reminders, urgent priority override, comments/moderation, encryption
and concurrency boundaries. Decisions and NFR renumbering:
[reconciliation note](reconciliation-2026-11-02.md). Tasks T3.1, T3.2, T3.3,
T3.6, T3.11–T3.13, T3.17, T3.19 and T3.20 are new or materially changed.

## Milestone 1 — Requirements & Design (due end of Week 3)

| # | Task | Output | Status |
|---|------|--------|--------|
| T1.1 | Read stakeholder brief; list ambiguities | [stakeholder-questions.md](stakeholder-questions.md) | Done (2026-10-19); Q13–Q17 added 2026-11-02 |
| T1.2 | Draft user stories + acceptance criteria | [requirements.md](requirements.md) | Done (2026-10-19); revision 3 (US-1…US-17, NFR-1…NFR-24) 2026-11-02 |
| T1.3 | Register assumptions and risks | [assumptions.md](assumptions.md), [risks.md](risks.md) | Done (2026-10-19); A-22…A-30 and R12–R16 added 2026-11-02 |
| T1.4 | Scaffold repository + Django skeleton; verify tests run | Runnable empty app + `manage.py test` green | Done (2026-10-19) |
| T1.5 | AI-use evidence log (requirements entries) | [ai-use-evidence-log.md](ai-use-evidence-log.md) | Done (2026-10-19); reconciliation entry AI-15 2026-11-02 |
| T1.6 | Reconcile supplied Requirements/Design documents against the course constraints | [reconciliation-2026-11-02.md](reconciliation-2026-11-02.md) | Done (2026-11-02) |
| T2.1 | Architecture diagram (components + data flow) | `docs/design/architecture.md` | Done (2026-10-19); Flutter + courses + comments 2026-11-02 |
| T2.2 | Data model / API contract (entities, key endpoints) | `docs/design/data-model-and-api.md` | Done (2026-10-19); Course/Section/Enrollment/Comment/priority fields 2026-11-02 |
| T2.3 | ADR-001: stack and deployment boundary | `docs/design/adr/ADR-001-stack-deployment-ui.md` | Done (2026-10-19); UI decision superseded (Flutter) 2026-11-02 |
| T2.4 | ADR-002: delivery simulation strategy (channel adapter) | `docs/design/adr/ADR-002-delivery-simulation.md` | Done (2026-10-19); 60 s SLA + mute bypass 2026-11-02 |
| T2.5 | Security, privacy, accessibility considerations note | `docs/design/security-privacy-accessibility.md` | Done (2026-10-19); encryption/concurrency boundary 2026-11-02 |
| T2.6 | Screen navigation map (role paths) | `docs/design/screen-navigation.md` | Done (2026-11-02) |
| T2.7 | Final M1 review: questions→AC trace, AI log completeness | M1 submission package | Week 3 |

## Milestone 2 — Implementation, Testing & Demo (due Week 8)

Ordered so the main workflow lands first (R7 mitigation) and the Flutter
toolchain risk (R12) surfaces early rather than in Week 7. Each task = small
AI-assisted increments, reviewed diffs, green tests before commit.

| # | Task | Covers | Target |
|---|------|--------|--------|
| T3.1 | **Flutter app scaffold:** navigation shell, API client, token storage, EN/AR resource skeleton, 360/390/430 layout harness; emulator talks to local Django API | NFR-14, NFR-19, NFR-20, R12 | Week 3–4 |
| T3.2 | Synthetic directory: seed command + People/Group/Department/Building models | US-2, NFR-1, A-10 | Week 4 |
| T3.3 | **Courses/sections/enrollments/faculty grants:** models, seed data, active-at-send resolution queries | US-14 (AC-14.1–14.3), A-22, R13 | Week 4 |
| T3.4 | Auth: login/logout, roles, PSU-shaped demo accounts, login-failure audit | US-9, NFR-21, A-3 | Week 4 |
| T3.5 | Alert compose + send pipeline (create → resolve audience incl. course/section → snapshot → category) | US-1, US-2 (AC-2.1–2.5), US-11 send side, US-14 compose | Week 4–5 |
| T3.6 | **Authorization choke-point:** officer scopes, faculty course grants, faculty severity boundary, 401/403 + audit on every rejection | US-3 (AC-3.1–3.8), US-14.4, NFR-1 | Week 5 |
| T3.7 | Channel adapters + simulated delivery dispatcher (per-recipient effective channels) + status queries + priority payload | US-4 (AC-4.1–4.6), US-12 dispatch side, US-16.2/16.3, NFR-7/NFR-23 | Week 5 |
| T3.8 | Device preferences + category opt-outs model, API and delivery tests (mandatory categories locked) | US-12 (AC-12.1–12.6) | Week 5 |
| T3.9 | Category management endpoints (comms_admin) + seeded bilingual vocabulary | US-11 (AC-11.1–11.5) | Week 5 |
| T3.10 | Recipient alert detail + read-status recording + lifecycle expiry | US-6 (AC-6.1–6.3), US-13 (AC-13.1–13.4), A-17 | Week 5–6 |
| T3.11 | **Comments:** post/list/soft-delete, recipient-only posting, plain-text validation, moderation by comms_admin | US-17 (AC-17.1–17.7), R14 | Week 6 |
| T3.12 | **Exam announcements + deadline reminders:** structured fields, 24–48 h window, idempotent `send_due_reminders` command | US-15 (AC-15.1–15.7), NFR-23 | Week 6 |
| T3.13 | **Urgent override + schedule changes:** `is_urgent`, `priority_source`, old/new pairs, deterministic ordering | US-16 (AC-16.1–16.7), NFR-8 | Week 6 |
| T3.14 | Recipient announcements + history + server-side filters (severity/category/read) | US-6, US-10 (AC-10.1–10.3) | Week 6 |
| T3.15 | Acknowledgment flow (critical only) + ack-rate read model | US-5 (AC-5.1–5.5) | Week 6 |
| T3.16 | Reporting + audit log + JSON/CSV export + faculty restricted report | US-7, US-8 (AC-7.1–7.5, 8.1–8.4) | Week 6–7 |
| T3.17 | **Flutter admin surfaces:** categories, sender/course grants, reports, audit export, comment moderation (no web dashboard) | US-7, US-8, US-11.2, US-17.4, NFR-14 | Week 7 |
| T3.18 | Misuse/boundary/concurrency test suite; criteria→test matrix; Flutter widget tests against the contract | Phase 4 portfolio, R4, NFR-1, NFR-24 | Week 6–7 |
| T3.19 | NFR/guard checks: log scrubbing, no-network guard, secret scan, demo reset, encryption/config guard, suite timing, license inventory | NFR-2, NFR-3, NFR-12, NFR-13, NFR-16–NFR-18, NFR-22 | Week 7 |
| T3.20 | **Bilingual EN/AR:** ARB resources + switcher, RTL `Directionality`, `name_ar` vocabulary, per-language date/number formatting, ARB parity + RTL tests | NFR-19, NFR-20, A-20, A-21, R11 | Week 6–7 |
| T3.21 | README, demo script, limitation list, license inventory, handoff checklist | Milestone 2 deliverables | Week 7 |
| T3.22 | Change request: impact analysis → focused change → regression evidence | Phase 5 (brief assigns after M1) | Week 7–8 |
| T3.23 | Reflection draft + oral-defense prep (every member explains system) | Milestone 2 deliverables | Week 8 |

*History: T3.1–T3.13 were the original Phase 3 list; T3.14–T3.17 added
2026-10-20 with the team feature-list expansion (US-9…US-13); T3.18 added the
same day with bilingual EN/AR. The 2026-11-02 revision renumbers the whole
Phase 3 list and adds Flutter, courses, comments, exam/deadline, urgency,
encryption/concurrency and the reconciliation task — see
[AI-use log](ai-use-evidence-log.md) AI-13, AI-14, AI-15.*

## Working agreements

- Commits are coherent increments tied to one task/AC group; no "build it all"
  prompts (see AI log entry AI-5, a rejected proposal of exactly that).
- Every code change is reviewed against its ACs before commit; tests are run
  (`manage.py test` and `flutter test`) and results noted in the commit body.
- Weekly review: progress, AI errors, evidence quality, top risks (from
  [risks.md](risks.md)).
- Stakeholder questions go through the instructor, consolidated in
  [stakeholder-questions.md](stakeholder-questions.md).
- The Flutter client never holds authorization, snapshot, priority or audit
  logic; those live in the Django service layer (AC-3.6, NFR-1).
