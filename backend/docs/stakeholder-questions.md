# Stakeholder Questions — PSU Alerts & Notifications

*Phase 1 deliverable. Per the project brief, questions are consolidated here and
routed through the instructor — we do not contact PSU units directly.
Revision 2026-11-02 adds questions raised by reconciling the supplied
Requirements and Design documents.*

Each question lists our **working recommendation** so the stakeholder can answer
with a yes/no or a correction instead of starting from scratch.

## Priority 1 — blocks requirements (Milestone 1)

| # | Question | Why it matters | Our recommendation |
|---|----------|----------------|--------------------|
| Q1 | Who is allowed to send an alert: University Communications only, or also departments/colleges? | Defines the authorization model and roles | Tiered: University Communications (all audiences) + designated alert officers scoped to their college/department + faculty scoped to their assigned courses/sections |
| Q2 | Does every alert require acknowledgment, or only urgent ones? | Acknowledgment drives recipient workflow and reporting | Acknowledgment required only for the highest severity level (`CRITICAL`) |
| Q3 | If someone misses an alert while it was active, should it disappear or remain viewable? | Determines alert lifecycle and history requirements | Alerts stay permanently in each recipient's personal history; only the "active/current" banner expires (24 h default) |
| Q13 | What should the comment moderation policy be? | Comments are in scope per the supplied docs | Only recipients of an alert may post; `comms_admin` may remove any comment (soft delete + audit); authors may remove their own. Plain text only, 1–500 chars. Any stricter policy is a policy setting, not a data-model redesign |
| Q14 | May faculty members send `CRITICAL` or campus-wide alerts, or are they limited to course alerts? | Design Doc §3.2 says medium/low; we added an "urgent" override for faculty but not `CRITICAL` | Keep faculty to `ADVISORY`/`INFORMATIONAL` for assigned courses/sections, allow `is_urgent` there, but reserve `CRITICAL` and campus-wide sends for `officer`/`comms_admin`. If PSU wants faculty to declare emergencies, that needs a separate escalation workflow and audit controls |

## Priority 2 — shapes the first release

| # | Question | Why it matters | Our recommendation |
|---|----------|----------------|--------------------|
| Q4 | How many severity levels make sense? | Stakeholder brief says "not sure yet" | Three: **Critical** (closure, safety threat), **Advisory** (schedule change, caution), **Informational** (workshop reminder). Urgent is a separate priority flag. |
| Q5 | Should recipients choose which channels they get (email / SMS / push), or does every alert go out on all selected channels? | Affects recipient profiles and delivery logic | Sender selects channels per alert; recipient enable/disable flags intersect per recipient for non-mandatory alerts. `CRITICAL`, exam, deadline and urgent alerts bypass mutes. |
| Q6 | Can an officer edit or cancel an alert after sending? | Affects audit trail design and API surface | No edits after send; a follow-up correction alert must be sent (keeps audit simple) |
| Q7 | What must the administrative report show, and who sees it? | "Basic administrative reporting" is vague | Per alert: sender, time, audience size, course/section (if any), per-channel delivery counts, read counts, acknowledgment rate (critical), comment counts. Visible to University Communications system-wide; faculty see only their own course alerts. |
| Q8 | Do recipients log in to the prototype, or do we demo with pre-opened sessions? | Brief says authentication is optional | Simple demo accounts (student / faculty / officer / comms admin); PSU-shaped synthetic identifiers; no real SSO in the prototype |
| Q9 | What is the default validity of an alert with no explicit end time? | Needed for the active/expired lifecycle | 24 hours |
| Q10 | Should the prototype use a real PSU org structure (colleges, buildings), or is a small invented taxonomy acceptable? | Data must be synthetic anyway | Invented but realistic taxonomy (e.g., 4 colleges, 6 buildings, ~60 synthetic people, courses/sections/enrollments) |
| Q11 | Should the prototype support languages other than English? | Scope, accessibility, and copy work | **Answered by team 2026-10-20 / confirmed 2026-11-02:** interface ships bilingual English/Arabic (NFR-19/NFR-20), RTL included; alert content stays sender-authored (A-20) |
| Q15 | Is real PSU SSO/OAuth expected in this prototype, or is a synthetic login acceptable? | Supplied docs say "PSU account" and also reference SSO as a service | Synthetic PSU-shaped accounts for the prototype; a real SSO/OAuth adapter is a documented handoff seam for any deployment beyond the course prototype |
| Q16 | Is "push within 1 minute" a hard requirement for the demo, or a target for a real deployment? | C-2 forbids a real gateway | For the prototype, the requirement is that simulated delivery rows reach terminal state and are visible within 60 s (NFR-23); real gateway timing is a handoff metric. |

## Priority 3 — can be answered during implementation

| # | Question | Why it matters | Our recommendation |
|---|----------|----------------|--------------------|
| Q12 | Duplicate or repeated alerts within a short window — worth suppressing? | Stakeholder did not mention it; possible Phase 5 change request | Not in first release; documented as a known gap |
| Q17 | Where does course/enrollment data come from at handoff, and is read-only sync acceptable? | Supplied docs require course/section targeting | Read-only import/sync from the student information system at handoff; the prototype uses synthetic data with replaceable Course/Section/Enrollment tables (A-22) |

## Explicit non-questions (agreed constraints, not open)

- No real student, faculty, or staff contact information anywhere — synthetic data only (C-3, C-5).
- No paid external services (no SMS gateway, no paid push, no paid email/SMS service); delivery is simulated locally (C-1, C-2).
- Local deployment is sufficient for the prototype; PSU security/privacy/accessibility review is required before any real use (C-4, C-6, NFR-6).
- No machine translation of alert content; interface is bilingual but title/body stay as entered (A-20).
- No web admin dashboard; all admin surfaces are in the Flutter mobile app (NFR-14).
- SQLite has no built-in encryption — a deployment boundary to document and guard (NFR-22).
- Alerts cannot be edited or cancelled after send (AC-1.4).
- Comments require recipients to post; moderation is logged (US-17).
