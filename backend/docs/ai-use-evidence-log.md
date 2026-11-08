# AI-Use Evidence Log — PSU Alerts & Notifications

*Phase 1 deliverable (requirements & design entries). Records important
interactions only — enough to reconstruct our reasoning, per the project brief.*

**Disclosure (per brief):** Provider: **opencode**; model: **big-pickle**
(`opencode/big-pickle`). Cost: none beyond course-provided access. One model
used throughout Phase 1. Limitations affecting this work are recorded inline
below and in the reflection (Phase 2+).

---

## Requirements phase

| ID | Objective and approach | What the AI contributed | Verification and decision |
|----|------------------------|--------------------------|----------------------------|
| AI-1 | Turn the ambiguous stakeholder brief into concrete questions | Read the brief and produced ~15 candidate questions covering the three open questions the stakeholder flagged (senders, acknowledgment, missed alerts) plus severity count, editing, expiry, reporting content, org taxonomy | Kept 12 after merging overlaps; sorted into three priority tiers by whether they block requirements ([stakeholder-questions.md](stakeholder-questions.md)). All questions carry a recommendation so the stakeholder can answer cheaply |
| AI-2 | Propose a severity model and acknowledgment rule | Recommended three levels (CRITICAL / ADVISORY / INFORMATIONAL) with acknowledgment required on CRITICAL only | **Kept as a recommendation, not a decision.** Marked OPEN-Q (Q2/Q4) in requirements and assumptions; written so a different answer is a config-level change (A-4/A-5). Not silently assumed — the brief forbids silent assumptions |
| AI-3 | Draft user stories and acceptance criteria from the brief's "common first release" list | Drafted US-1…US-8 with ~30 acceptance criteria, each phrased as an HTTP-status/count/snapshot assertion so tests can be written directly against them | Reviewed criterion by criterion. Added AC-2.3 (reject sends that resolve to zero recipients) as a team safeguard the stakeholder never asked for — kept because silent empty sends are exactly the "we're never sure who saw it" failure the brief describes. Traceability seed table added to [requirements.md](requirements.md) |
| AI-4 | Register assumptions and risks | Produced a 16-row assumption table (each with status and "consequence if wrong") and a 10-row risk register | Kept. Split assumptions into working vs. open so unanswered stakeholder questions are visible rather than buried. R4 (AI code weakening authz checks) was added after review of the brief's "system controls" section |

## Design phase (Phase 2)

| ID | Objective and approach | What the AI contributed | Verification and decision |
|----|------------------------|--------------------------|----------------------------|
| AI-8 | Shape the architecture around the brief's hardest constraint: authorization must be real, not cosmetic | Proposed a **single service-layer choke-point** with the server-rendered UI and the REST API as interchangeable thin clients, plus a send sequence that treats a denied send as a first-class audited event | **Kept.** Motivated directly by AC-3.6/NFR-2: one place to enforce scopes, and the independent API tests then prove the same path the UI uses. Recorded in [architecture.md](design/architecture.md) |
| AI-9 | **Corrected draft:** delivery records carrying contact data | The first data-model draft copied recipient email/phone onto each DeliveryRecord "so the payload is self-contained" | **Corrected before commit:** DeliveryRecords hold FK + status only; contact fields live once on Profile. Rationale: NFR-1/NFR-4 — a self-contained delivery row is exactly how contact data multiplies into logs and exports. See [data model](design/data-model-and-api.md) |
| AI-10 | **Rejected proposal:** async task queue for delivery | The first architecture draft included Celery (or equivalent) so the QUEUED→DELIVERED transition runs in a worker | **Rejected for v1.** ~60 synthetic recipients do not justify broker ops; synchronous dispatch keeps demos deterministic. The state machine stays async-ready — consequence recorded in [ADR-002](design/adr/ADR-002-delivery-simulation.md) so the rejection is auditable, not forgotten |
| AI-11 | Justify the stack instead of assuming it | Produced the alternatives table behind [ADR-001](design/adr/ADR-001-stack-deployment-ui.md): Node+React SPA, Flask/FastAPI, PostgreSQL, Docker/HTTPS proxy, API-only vanilla JS — each rejected with a stated cost | **Kept.** Every consequence the team accepts (dev secrets in repo under local boundary, SQLite concurrency, template UI) is written down so reviewers can challenge a specific tradeoff rather than the vibe |
| AI-12 | **Revision:** NFR backlog review and mobile-only pivot (2026-10-20) | AI drafted a ~20-item NFR backlog; the team accepted NFR-13…29 (timeliness, transactional send, state immutability, historical integrity, demo reset, fail-fast config, channel extensibility, suite properties, license hygiene, secret scanning) and **changed NFR-23 from "responsive at phone widths" to mobile-phone-only** | Deferred candidates recorded in [requirements.md](requirements.md) with preserved numbering. ADR-001 UI decision amended with the accepted consequence (no desktop layout maintained) — the revision is visible in the ADR history line, not silently overwritten |
| AI-13 | **Revision:** team feature list folded into requirements (2026-10-20) | The team supplied nine features (authorization/login, delivery, data protection, view announcements, filtering, categorization, device preferences, read status, history). AI mapped them to existing US/NFRs (5 already covered) and drafted US-9…US-13 for the genuinely new ones, including a feature→requirement trace table | **Kept, with two flagged judgment calls:** (1) *Read status* modeled as a view receipt **distinct from acknowledgment** (AC-13.2, A-17) — resolves the standing R10 risk that demos overclaim "ack = read"; (2) *Device preferences* reversed the earlier Q5 out-of-scope recommendation — Q5 annotated as superseded, A-18 makes the portal an always-on channel so empty preference intersections aren't data loss. Model/API revision appended to the contract (not overwritten); tasks T3.14–T3.17 added. Templates deliberately left as stretch |
| AI-14 | **Revision:** bilingual English/Arabic interface (2026-10-20) | Team decided the application must run in EN and AR. AI proposed NFR-31 (interface coverage, switcher, per-language formatting) and NFR-32 (RTL correctness at mobile widths); superseded A-11 and Q11; amended ADR-001 noting the decision reinforces the server-rendered choice (Django i18n needs no client framework) | **Rejected proposal recorded:** AI floated auto-translating alert title/body into each reader's language. Team rejected — runtime translation requires an external service (violates C1/C16) and a mistranslated CRITICAL safety message is itself a hazard. Settled as A-20: content is sender-authored, interface is bilingual. Schema impact contained: `name_en`/`name_ar` on Category (A-21), language cookie — no change to alert storage. Task T3.18 added |
| AI-15 | **Revision:** reconcile the supplied Requirements and Design documents with the existing baseline (2026-11-02) | Two large documents arrived after Phase 2. AI extracted the functional requirements, roles, use cases, NFRs, architecture, navigation and ER model, then produced an explicit conflict list instead of merging silently. Decisions: **Flutter replaces server-rendered templates** (Design Doc §1–3); Firebase/APNs, PSU SSO and PostgreSQL stay handoff items because of C-1…C-5; faculty may send ADVISORY/INFORMATIONAL to assigned courses and set `is_urgent`, while CRITICAL and campus-wide sends stay with officers/comms_admin; comments adopted with soft-delete moderation; category opt-outs allowed except mandatory/urgent/exam/deadline; "push within 1 minute" restated as a 60 s simulated-delivery SLA; "PSU account" and "encrypted at rest" restated as boundaries. NFRs compacted to NFR-1…NFR-24; added US-14…US-17, A-22…A-30, Q13…Q17, R12…R16, and a screen-navigation document | **Kept, with the contradictions made explicit.** Every adopted choice is recorded in [reconciliation-2026-11-02.md](reconciliation-2026-11-02.md) with its authority; rejected items (real gateways, web dashboard, SSO in v1, SQLCipher-in-demo, faculty CRITICAL) each have a stated reason. **Rejected proposal recorded:** AI initially drafted the Design Doc's §4–6 stack literally (Firebase/APNs + PostgreSQL + SSO + web admin), which would have violated the no-budget/no-real-gateway constraints and contradicted §1–2. Team kept §1–2. Historical entries AI-8, AI-11, AI-12 and AI-14 keep their old NFR numbers and their server-rendered-template wording on purpose — this log is not rewritten; the current baseline is [requirements.md](requirements.md) revision 3 |

> **Numbering note (2026-11-02):** live documents use NFR-1…NFR-24. Entries
> AI-12 and AI-14 reference the older NFR-13…NFR-32 scheme and the
> server-rendered UI decision; they are preserved as written because they
> record what was decided at that time. AI-15 is the reconciliation point.

## Planning phase

| ID | Objective and approach | What the AI contributed | Verification and decision |
|----|------------------------|--------------------------|----------------------------|
| AI-5 | **Rejected proposal:** scaffolding the repository | The AI considered generating the full alerts implementation (models, views, delivery worker, tests) in the same pass as the empty-project scaffold, to "save a round trip" | **Rejected.** The brief requires coherent increments and reviewed diffs; a big-bang generation would have produced code no one could defend. Skeleton only (settings, empty `alerts` app, smoke test); business logic deferred to Phase 3 tasks T3.1+ ([task-plan.md](task-plan.md)) |
| AI-6 | **Corrected assumption:** whether to build on `taskflow-api` | Initial exploration flagged the existing `taskflow-api` folder as a possible starter codebase for the PSU prototype | **Corrected after inspection:** taskflow-api is the unrelated Week 4 tutorial (two-step 2FA login, no alerting domain). PSU Alerts starts from an empty repository; nothing was reused. Recorded so the decision is auditable |
| AI-7 | Environment setup when Git was missing | AI checked common install paths and winget availability, then asked before installing Git 2.55 via winget | Install approved by the team member and executed; repo initialized with meaningful commits immediately after ([task-plan.md](task-plan.md) R8 tracks this risk as resolved) |

## Standing self-check (applies to every future entry)

- Every AI-suggested requirement change must land in `docs/` **before** the
  matching code (this log is the evidence trail).
- Any AI-generated code touching roles, audiences, or acknowledgment is
  reviewed against the AC IDs and covered by independently written tests
  (Phase 4, R4).
- Entries record rejections, not just acceptances — an all-green log is a
  failed log.
