# Stakeholder Requirements — PSU Alerts & Notifications

*Phase 1 deliverable, revision 3 (2026-11-02). Derived from the University
Communications brief (2026-10-19), the supplied **`Requirments Doc.md`**
(functional requirements, roles, user stories, use cases, acceptance criteria)
and **`Design Doc.md`** (architecture, stack, navigation), reconciled with the
course constraints C-1…C-6 and [assumptions.md](assumptions.md).*

**Status legend:** each requirement cites the assumption it rests on
([assumptions.md](assumptions.md)). Items marked **OPEN-Q** depend on a
stakeholder answer; the version below is our recommendation and is written so
tests can be written against it now and adjusted cheaply later.

**Revision history**

| Revision | Date | Change |
|----------|------|--------|
| 1 | 2026-10-19 | US-1…US-8, NFR-1…NFR-7 from the stakeholder brief |
| 2 | 2026-10-20 | Added US-9…US-13, category/device/read/filter features, bilingual EN/AR |
| 3 | 2026-11-02 | Aligned to the supplied Requirements and Design documents: Flutter mobile client, Faculty course/section alerts, exam/deadline reminders, urgent priority override, comments with moderation, PSU-account-shaped login, encryption boundary, 1-minute delivery SLA, concurrency target; NFR numbering compacted to NFR-1…NFR-24. Conflicts and resolutions: [reconciliation](reconciliation-2026-11-02.md) |

## Scope (first release)

**In scope:** Flutter mobile app (360–430 logical px, Android/iOS emulator);
PSU-account-shaped login and sessions; role and audience authorization;
alert composition with severity **and** category; urgent priority override;
audience targeting (campus, role, department, building, group, course,
section); Faculty course/section alerts; structured exam announcements;
academic deadline reminders; class/section schedule changes; simulated
multi-channel delivery with status; device and category preferences;
read status; critical acknowledgment; per-user history with filtering;
comments with moderation; administrative and audit reporting; bilingual
English/Arabic interface including RTL.

**Out of scope for v1 / PSU handoff** (kept explicit, not silently dropped):

- Real SMS, push (FCM/APNs), email gateways, and any paid service (C-1, C-2).
- Real PSU SSO/OAuth and real PSU directory data (C-3, C-5). Login uses local
  synthetic accounts shaped like PSU accounts (NFR-21).
- Machine translation of alert content. The **interface** is bilingual; alert
  title/body are authored and stored as entered (A-20).
- Alert approval workflows, duplicate suppression, recipient-authored
  templates. Templates remain a stretch item.
- A separate web admin dashboard; all admin surfaces are screens inside the
  Flutter app (mobile-only constraint).
- PostgreSQL/MySQL, Firebase/APNs, production HTTPS termination and encrypted
  storage: described as the PSU deployment boundary, not built into the local
  prototype (NFR-22). Post-send editing is never allowed (US-1, AC-1.4).

**Document conflicts resolved** (details and rationale in
[reconciliation-2026-11-02.md](reconciliation-2026-11-02.md)):

| Conflict | Resolution |
|----------|------------|
| `Design Doc.md` §4–6 names Firebase/APNs, PSU SSO/OAuth, PostgreSQL and a web dashboard; §1–2 says Flutter + Django + SQLite + simulated delivery | §1–2 is the team decision; Firebase/APNs/SSO/PostgreSQL/web dashboard are PSU handoff, rejected for v1 by C-1…C-5 and NFR-2/NFR-14 |
| `Design Doc.md` §3.2: Faculty may send only medium/low severity; `Requirments Doc.md`: Faculty may mark an alert Urgent | Faculty may send `ADVISORY`/`INFORMATIONAL` to their own courses and may set `is_urgent` (priority override). `CRITICAL` and campus-wide sends stay with Alert Officers / Comms Admin (US-14, US-16) |
| `Requirments Doc.md`: push delivered "within 1 minute"; C-2: no real gateway | Delivery is simulated; the measurable requirement is that every simulated delivery row is terminal within 60 s, and a campus CRITICAL send completes ≤2 s (NFR-7, NFR-23) |
| `Requirments Doc.md`: login "based on PSU account"; C-3/C-5: synthetic data only | Local accounts use PSU-shaped identifiers (`student ID`/username) but synthetic credentials; a real SSO adapter is a handoff seam (NFR-21) |
| `Requirments Doc.md`: data "encrypted at rest"; SQLite has no built-in encryption | The prototype stores synthetic data only; any non-local deployment must use an encrypted volume or SQLCipher and HTTPS. This is a documented boundary with a startup guard, not a claim about the demo (NFR-22) |
| `Requirments Doc.md` asks for event opt-out, but exam/urgent alerts must not be muted | Category preferences apply to `EVENT` and `OTHER`; `EXAM`/schedule-change/urgent/CRITICAL bypass mutes (US-12, US-16) |

## Architecture summary (three-tier)

The system uses a **three-tier client–server architecture**:

| Tier | Component | Owns |
|------|-----------|------|
| Presentation | **Flutter** mobile app | Rendering, navigation, bilingual EN/AR + RTL, calling the API. Holds no authorization logic and is never trusted. |
| Application | **Django** (views → service layer → models) | Authentication and login, role resolution, alert creation, audience/group selection and snapshotting, delivery simulation, acknowledgment tracking, rejection and audit logging. |
| Data | **SQLite** (synthetic records only) | Users/profiles and role grants, directory/groups, courses and enrollments, alerts and recipient snapshots, delivery records, acknowledgments, comments, audit log. |

Every security-relevant operation is performed by the Django application
layer, so the same rules apply whether a request comes from the Flutter app or
from a direct API client. Rejected requests (wrong role, wrong audience,
wrong course, unauthenticated) are refused with **HTTP 401/403 and recorded in
the audit log** — rejection is an auditable event, not a silent failure
(AC-3.2, AC-3.8, AC-9.3, NFR-5).

## Team feature list → requirements trace

Team scope decision 2026-10-20, extended 2026-11-02 (see
[AI-use log](ai-use-evidence-log.md) AI-13, AI-15):

| Team feature | Requirements |
|--------------|--------------|
| Authorization and Login | US-9 (login/session) + US-3, US-8 (authorization) + NFR-21 |
| Notification Delivery | US-4, modulated per-recipient by US-12, accelerated by US-16; NFR-7, NFR-23 |
| Data Protection | NFR-1, NFR-3, NFR-22, AC-6.4, AC-7.4, AC-12.5 |
| View Announcements | US-6 (active view + detail) with NFR-14 |
| Filter Notifications | US-10 |
| Categorize Notifications | US-11 (category axis alongside severity) |
| Device Preferences | US-12 |
| Read Status of Notifications | US-13 |
| Notification History | US-6 |
| Course / section alerts | US-14 + US-2 (`course`, `section` selectors) |
| Exam and deadline reminders | US-15 |
| Urgent priority override | US-16 + US-8, US-12 |
| Comments and moderation | US-17 |

## Roles

Role-based authorization resolves every account to one of **three role
families — Student, Faculty, Admin** — and the backend derives that user's
permitted parameters from it. "Admin" is an umbrella family containing two
operational levels (`officer` and `comms_admin`); the finer split is what lets
an Alert Officer send only within granted scopes while a Communications Admin
can send anywhere. All authorization is decided server-side.

| Role family | Role | Code | Capabilities |
|-------------|------|------|--------------|
| **Student** | Student | `student` | Receive targeted alerts, acknowledge critical alerts, comment on received alerts, manage channel/category preferences, view own history |
| **Faculty** | Faculty | `faculty` | All student capabilities; send `ADVISORY`/`INFORMATIONAL` alerts to **courses/sections they are assigned to**, optionally marked urgent; create exam announcements and deadline reminders for those courses; view delivery/read/ack counts for their own course alerts |
| **Admin** | Alert Officer (Campus Safety) | `officer` | Compose and send alerts **within authorized audiences only**; any severity; view delivery and acknowledgment status within scope |
| **Admin** | Communications Admin | `comms_admin` | All officer capabilities; send to any audience; manage categories, officer/faculty sender grants, comments, reports and audit log |
| Review only | PSU IT | `psu_it` | Read-only review of security, privacy, architecture and deployment readiness; no send or moderation rights in the prototype (review role, not a runtime data role) |
| Process only | Development Team | n/a | Build, test and maintain the prototype; not an application login role |

All enforcement is server-side; the Flutter client is not trusted (NFR-1,
AC-3.6). `psu_it` and the development team are review/process roles; they do
not receive alert-delivery privileges. The three role families above are the
only *sending/recipient* identities in v1 — no additional role family is
introduced by a client request.

## Severity and priority model

Three severity levels, mapped to the Design Doc's high/medium/low wording:

| Severity | Design Doc wording | Acknowledgment | Who may send | Example |
|----------|--------------------|----------------|--------------|---------|
| `CRITICAL` | High | **Required** | `officer`, `comms_admin` | "Campus closed due to snow — all classes cancelled" |
| `ADVISORY` | Medium | Not required | `officer`, `comms_admin`; `faculty` for own courses | "Lab building closed for maintenance until Friday" |
| `INFORMATIONAL` | Low | Not required | `officer`, `comms_admin`; `faculty` for own courses | "Workshop registration opens Monday" |

Two orthogonal presentation flags sit beside severity:

- `is_urgent` — high-priority override. Any sender who may send the alert may
  set it, but Faculty only on their own course/section alerts. Urgent alerts
  cannot be muted, use a distinct sound/vibration payload, and sort above
  non-urgent alerts of the same severity (US-16).
- `priority_source` — derived from content: `EXAM` for exam announcements,
  `SCHEDULE` for schedule changes, `URGENT` when `is_urgent`, otherwise
  `NORMAL`. `EXAM` and `SCHEDULE` also bypass category mutes (US-15/US-16).

Acknowledgment is required for `CRITICAL` only (OPEN-Q, Q2). Reading is never
the same as acknowledgment (AC-13.2).

---

## User stories and acceptance criteria

### US-1 — Compose and send an alert *(officer / comms_admin / faculty)*

> As an authorized sender, I can compose an alert with a title, body, severity,
> category and target audience and send it, so that the campus community is
> informed of urgent events without scrambling across email and WhatsApp.

- **AC-1.1** A valid send request (title, body, severity, category, audience,
  channels) returns HTTP 201 and persists an alert record containing the
  sender's user ID, a server timestamp, and a system-assigned alert ID.
- **AC-1.2** A send request missing any required field returns HTTP 400 with a
  field-level error message and creates **no** alert record.
- **AC-1.3** Sending with an unknown/invalid severity or category value returns
  HTTP 400; the set of accepted values is exactly the configured list.
- **AC-1.4** Alerts cannot be edited or cancelled after send; any edit attempt
  on a sent alert returns HTTP 405/409 and leaves the record unchanged.
- **AC-1.5** `is_urgent` and `priority_source` are stored at send time and are
  immutable; a follow-up alert is required to change priority (US-16).

### US-2 — Target an audience *(officer / comms_admin / faculty)*

> As an authorized sender, I can target an alert to the people who need it —
> everyone on campus, one department, one building, one role, one group, one
> course or one section — so that people only get messages relevant to them.

- **AC-2.1** The system supports audience selectors: `everyone`, `role`
  (students / faculty / employees), `department`, `building`, `group`,
  `course`, and `section`. Each send request names exactly one selector in v1.
- **AC-2.2** At send time the audience is resolved against the synthetic
  directory and enrollment data; a fixture-based test asserts that a known
  selector resolves to the expected set of recipients (e.g.,
  `section=CS-101-01` → N known students; `department=Engineering` → N known
  users).
- **AC-2.3** An audience selector that resolves to **zero** recipients is
  rejected with HTTP 400 ("no recipients match") and no alert is created —
  prevents silently sending into the void.
- **AC-2.4** Every alert stores a snapshot of the resolved recipient list at
  send time, so later directory/enrollment changes cannot rewrite history.
- **AC-2.5** `course` and `section` selectors are available only to senders
  authorized for that course/section (US-3, US-14); a `faculty` sender cannot
  select `everyone`, a department, or a building in v1.

### US-3 — Authorization: send only within scope *(officer / comms_admin / faculty)*

> As an authorized sender, I can send only to the audiences I am authorized
> for, and the system records who sent what and when — so that a single
> department cannot accidentally (or deliberately) message the whole campus.

- **AC-3.1** Each officer has a stored set of authorized audience scopes
  (e.g., `department=Engineering`, `building=ScienceHall`); each faculty
  member has stored course/section grants. Scopes and grants are assigned by a
  `comms_admin`.
- **AC-3.2** A send request whose audience falls outside the sender's scopes
  returns HTTP 403, is **not** delivered, and is written to the security audit
  log with the sender ID and requested audience.
- **AC-3.3** A `comms_admin` may send to any audience. An `officer` may send
  any severity within scope. A `faculty` sender may send only
  `ADVISORY`/`INFORMATIONAL` to an assigned course/section.
- **AC-3.4** A `student` calling any send/management endpoint receives HTTP
  403.
- **AC-3.5** Only a `comms_admin` can create/update officer scopes and faculty
  course/section grants; any other role attempting this receives HTTP 403.
- **AC-3.6** Authorization is enforced in the API layer regardless of client;
  no criterion depends on Flutter-side behavior.
- **AC-3.7** Faculty course/section grants are re-checked on every send; a
  revoked assignment produces HTTP 403 on the next attempt (AC-8.2).
- **AC-3.8** **Every** request rejected for role or audience reasons — not
  only sends — returns HTTP 401/403, reveals no protected data, and is written
  to the audit log with the actor ID (or `anonymous`), the endpoint/action,
  the requested object ID, the reason, and a server timestamp. Rejections are
  never silently dropped (NFR-5).

### US-4 — Simulated delivery with status tracking *(system)*

> As University Communications, I can see whether an alert was actually
> delivered to recipients on each channel — without paying for SMS or push
> services.

- **AC-4.1** On successful send, the system creates one delivery record per
  recipient per effective channel, initially `QUEUED`.
- **AC-4.2** A simulation worker transitions records to `DELIVERED` or
  `FAILED`; **no external network call is ever made**: email goes to the
  Django console/locmem backend, SMS and push append to a local simulated
  outbox (log file or table).
- **AC-4.3** Delivery status is queryable per alert: totals per
  state/channel, and per-recipient detail for senders with scope over that
  alert (faculty see only their own course alerts).
- **AC-4.4** A deterministic failure rule exists for testing (e.g., channel
  `sms` fails for recipients whose synthetic profile flags "no mobile"), so
  the FAILED path is exercised in automated tests, not just left in code.
- **AC-4.5** All delivery records for a normal send reach a terminal state
  within **60 s** of the send request, measured from the server timestamp
  (NFR-23). In the synchronous v1 implementation this is effectively immediate
  and the test asserts the elapsed time.
- **AC-4.6** For urgent/exam/schedule-change alerts, the simulated push
  payload includes the priority values (`sound`, `vibration_pattern`,
  `bypass_mute=true`) so the Flutter client can render a distinct alert
  (US-16, AC-16.3).

### US-5 — Acknowledgment of critical alerts *(recipient / officer)*

> As University Communications, I know whether the people who had to see a
> critical alert actually saw it — not just that we pressed send.

- **AC-5.1** Only `CRITICAL` alerts require acknowledgment (OPEN-Q, Q2).
- **AC-5.2** A recipient acknowledging a critical alert they were sent records
  the recipient ID and an immutable server timestamp; repeat acknowledgment of
  the same alert returns HTTP 200/409 without creating a duplicate record.
  Acknowledgment also marks the alert read (AC-13.2).
- **AC-5.3** Acknowledging an alert that was **not** sent to that recipient,
  or that is not critical, returns HTTP 403/400.
- **AC-5.4** The sender (within scope) and `comms_admin` can read the
  acknowledgment rate of an alert: `acknowledged_count / recipient_count`,
  plus the list of who has not yet acknowledged.
- **AC-5.5** Faculty may read acknowledgment counts only for critical alerts
  they were authorized to send; faculty cannot send `CRITICAL` in v1, so their
  course alerts have no ack requirement (US-14).

### US-6 — Recipient history and announcements *(recipient)*

> As a student or employee, if I missed an alert while it was active, I can
> still look it back up — so a closure notice I saw too late doesn't vanish.

- **AC-6.1** Each alert carries a lifecycle state: `ACTIVE` until its expiry
  (explicit or default 24 h per Q9), then `EXPIRED`. Expiry is automatic and
  does not delete anything.
- **AC-6.2** A recipient can list their own history: every alert resolved to
  them, newest first, each showing severity, category, expiry state, delivery
  status, read state, and (for critical) whether they acknowledged it.
- **AC-6.3** Expired alerts remain fully readable in history (title, body,
  timestamps, comments unless moderated away).
- **AC-6.4** A recipient can read only alerts that were sent to them; requests
  for other recipients' history return HTTP 403.
- **AC-6.5** The recipient announcements view lists currently `ACTIVE` alerts
  above older history, ordered by priority then recency: `CRITICAL`, then
  urgent/exam/schedule-change, then lower severities (NFR-8). A missed alert is
  visible the moment the app opens.
- **AC-6.6** Course alerts show course code, course title, and section; exam
  and deadline alerts show their structured fields (US-15) in both the list
  summary and the detail view.

### US-7 — Administrative and audit reporting *(comms_admin)*

> As University Communications, I can pull a report of what was sent, to whom,
> and who acknowledged — the institutional record the brief asks for.

- **AC-7.1** `comms_admin` can list all alerts system-wide with sender,
  timestamp, severity, category, audience selector, and resolved recipient
  count.
- **AC-7.2** For any single alert, the report includes per-channel delivery
  counts (queued/delivered/failed), read counts, comment counts, and, for
  critical alerts, acknowledgment counts.
- **AC-7.3** An audit log records every send attempt (successful or denied),
  authorization/grant change, comment moderation action, and acknowledgment
  with actor ID and timestamp; it is readable by `comms_admin` and exportable
  as JSON or CSV.
- **AC-7.4** The report and audit endpoints return HTTP 403 for
  `student`/`faculty`/`officer` roles.
- **AC-7.5** Faculty can read a restricted report for their own course alerts
  only: per-channel counts, read counts and comments; no system-wide data.

### US-8 — Sender authorization administration *(comms_admin)*

> As University Communications, I can designate who may send alerts and to
> which audiences, answering "should departments send their own?" with a
> controlled yes.

- **AC-8.1** A `comms_admin` can grant/revoke audience scopes for any user,
  promote them to `officer`, and grant/revoke faculty course/section sending
  grants; changes are audit-logged.
- **AC-8.2** Revoking a scope or course grant takes effect on the next send
  attempt (no queued work continues under old authorization).
- **AC-8.3** Authorization state is readable via API by `comms_admin` only.
- **AC-8.4** A user may hold `faculty` plus course grants without becoming an
  `officer`; the two authorization paths are independent and both are
  server-checked.

### US-9 — Login and session *(any user)*

> As a student, faculty member, officer, or communications admin, I log in with
> my PSU-shaped demo account so that the system knows who I am — and only I can
> act as me.

- **AC-9.1** Valid PSU-shaped username/ID and password returns HTTP 200 with
  an auth token; invalid credentials return HTTP 401 without revealing whether
  the username or the password was wrong.
- **AC-9.2** Logout invalidates the token/session; reusing it afterwards
  returns HTTP 401.
- **AC-9.3** Failed login attempts are written to the audit log
  (`LOGIN_FAILED`, actor + timestamp; AC-7.3 vocabulary).
- **AC-9.4** Every endpoint except login and `/api/health/` requires
  authentication (HTTP 401 when anonymous).
- **AC-9.5** Accounts are local and synthetic but use PSU-shaped identifiers;
  no real PSU credential or directory record is stored (NFR-21, C-3/C-5).

### US-10 — Filter notifications *(recipient / officer)*

> As a recipient, I can filter my notifications by severity, category, and
> read state, so that I can find what matters without scrolling an archive.

- **AC-10.1** The recipient history/announcements endpoint accepts filter
  query parameters `severity`, `category`, and `read`
  (`true|false`); filters combine with AND and are applied server-side.
- **AC-10.2** The sender alert list accepts `severity`, `category`,
  `audience_type`, and `course` filters, always scoped to what that sender may
  see (US-3 boundaries unaffected by filtering).
- **AC-10.3** An invalid filter value returns HTTP 400; unknown parameters
  are ignored, not silently mis-applied.

### US-11 — Categorize notifications *(comms_admin / all)*

> As University Communications, I can maintain alert categories (closure,
> safety, event, schedule…) so that recipients can tell a snow closure from a
> workshop notice beyond just the severity label.

- **AC-11.1** Every alert carries exactly one category from the active
  category list; category is a required send field (AC-1.2 applies);
  severity and category are independent axes (a SAFETY alert may be
  ADVISORY).
- **AC-11.2** A `comms_admin` can create, rename, and deactivate categories;
  changes are audit-logged; deactivated categories cannot be selected for
  new alerts, and historical alerts keep the category they were sent with.
- **AC-11.3** Recipients see the category on every surface: announcement
  list, alert detail, and history.
- **AC-11.4** Seeded default vocabulary: `CLOSURE`, `SAFETY`, `EVENT`,
  `SCHEDULE`, `OTHER`, plus the course-specific `EXAM` and `DEADLINE`
  (A-19/A-22). Exam/deadline are content types, not extra severity levels.
- **AC-11.5** Category labels are stored bilingually (`name_en`, `name_ar`);
  the Flutter client displays the label for the active language (NFR-19).

### US-12 — Device and category preferences *(recipient)*

> As a recipient, I can choose which channels and topics actually reach my
> device, so that an urgent alert doesn't just pile up in an inbox I ignore —
> while the portal always shows everything.

- **AC-12.1** Each recipient can enable or disable `EMAIL`, `SMS`, and
  `PUSH` independently; all default to enabled. The in-app portal/announcements
  view is always on and is not a preference (A-18).
- **AC-12.2** A recipient can opt out of non-mandatory categories (`EVENT`,
  `OTHER`); opt-outs affect future deliveries only and never rewrite existing
  delivery records (aligns with NFR-10/AC-2.4).
- **AC-12.3** On send, each recipient's effective channels = sender-selected
  channels ∩ recipient-enabled channels, minus channels suppressed by a
  category opt-out. `EXAM`, `DEADLINE`, schedule-change, urgent and `CRITICAL`
  alerts bypass category opt-outs (US-15/US-16).
- **AC-12.4** A recipient whose intersection is empty still appears in the
  snapshot with portal-only visibility — this is not an error and produces
  no EMAIL/SMS/PUSH records.
- **AC-12.5** Users can read and change only their own preferences
  (HTTP 403 otherwise); senders cannot inspect recipients' preferences.
- **AC-12.6** Faculty and staff may opt out of `EVENT`/`OTHER` like students;
  mandatory safety/closure/exam categories are never suppressible.

### US-13 — Read status *(recipient / sender)*

> As a recipient, opening an alert marks it read, so that my list shows what
> I have and haven't seen — and senders can see whether critical alerts
> were merely delivered or actually opened.

- **AC-13.1** Viewing an alert's detail marks it read for that recipient and
  records a server-side `read_at` timestamp; repeat views do not create
  duplicate records (idempotent).
- **AC-13.2** Read state is **distinct from acknowledgment**: reading never
  satisfies the critical-ack requirement (AC-5.1), but acknowledging an
  alert implies it has been read (AC-5.2).
- **AC-13.3** Lists and details show read/unread state; the `read` filter
  (AC-10.1) operates on this state.
- **AC-13.4** Only the recipient themselves can mark their alerts read
  (HTTP 403 otherwise); senders may **view** read/unread counts per alert
  within their scope but cannot mutate read state.

### US-14 — Faculty course and section alerts *(faculty)*

> As a faculty member, I want to post alerts only to students enrolled in my
> courses/sections so that the right students receive the information.

- **AC-14.1** A `faculty` sender sees only the courses/sections they are
  assigned to; the API rejects a course/section outside those grants with HTTP
  403 and audits the attempt.
- **AC-14.2** A course alert requires `course` (and optional `section`), title,
  body, category, severity and channels; missing fields return HTTP 400 with
  field-level errors and create no record.
- **AC-14.3** Recipients are resolved from **active enrollments** at send time
  and snapshotted; later enrollment changes do not rewrite the send
  (AC-2.4, NFR-11).
- **AC-14.4** Faculty may send `ADVISORY`/`INFORMATIONAL` only; a `CRITICAL`
  send returns HTTP 403. Faculty may set `is_urgent` (US-16).
- **AC-14.5** The alert stores and displays course code, course title, section
  and the instructor of record, so a student can identify the course.
- **AC-14.6** A faculty member can read delivery/read counts and comments for
  their own course alerts only (AC-4.3, AC-7.5).
- **AC-14.7** A student not enrolled in the target course/section at send time
  is never in the snapshot, even if they enroll immediately afterwards.

### US-15 — Exam announcements and academic deadline reminders *(faculty / system)*

> As a student, I want to know when, where and what the exams are, and I want
> academic deadline reminders, so that I can prepare and not miss anything.

- **AC-15.1** An exam announcement requires `course`, `exam_date`,
  `exam_time`, `exam_location`, and `instructions` (may be empty text) in
  addition to the standard fields; missing structured fields return HTTP 400.
- **AC-15.2** Exam announcements derive `priority_source=EXAM` and are treated
  as high priority: they bypass category opt-outs and always create a portal
  row plus a simulated push record (AC-12.3).
- **AC-15.3** A deadline reminder requires `course`, `deadline_at`, and
  `remind_at`; `remind_at` must be 24–48 h before `deadline_at` (configurable
  window), otherwise HTTP 400. The reminder text is stored with the alert.
- **AC-15.4** Reminders are dispatched by a local management command
  (`manage.py send_due_reminders`), not an external scheduler; each
  (alert, recipient) reminder is sent once, and re-running the command is
  idempotent.
- **AC-15.5** The reminder becomes visible in the recipient's history when
  dispatched, with the deadline timestamp and course identity; it follows the
  same delivery/read rules as other alerts.
- **AC-15.6** Either a faculty member (for an assigned course) or the system
  (from seeded course deadline data) may create a reminder; system-created
  reminders have a null human sender but a non-null `created_by_system` marker
  for audit.
- **AC-15.7** Exam and deadline alerts remain readable after expiry; deleting
  a course does not remove historical alerts or their snapshots (NFR-11).

### US-16 — Urgent priority override and schedule changes *(sender / recipient)*

> As a faculty member or administrator, I want to mark an alert "Urgent" so
> that it gets higher priority and a distinct notification, and I want schedule
> changes to identify both the old and the new arrangement.

- **AC-16.1** `is_urgent=true` is accepted from `officer`/`comms_admin` for any
  alert, and from `faculty` only for an assigned course/section and only on
  `ADVISORY`/`INFORMATIONAL`; other attempts return HTTP 403.
- **AC-16.2** Urgent alerts cannot be muted: channel and category preferences
  cannot suppress the portal row or the simulated push record; the effective
  push channel is forced on (AC-12.3).
- **AC-16.3** The simulated push payload for urgent alerts carries a distinct
  `sound` and `vibration_pattern` plus `bypass_mute=true`; normal alerts carry
  the default values. Automated tests assert the payloads differ.
- **AC-16.4** Ordering is deterministic: `CRITICAL` first, then
  urgent/exam/schedule-change, then `ADVISORY`, then `INFORMATIONAL`; within a
  band, newest first. Lower severities never displace an active critical alert
  (NFR-8).
- **AC-16.5** Urgent/exam/schedule-change priority is immutable after send; a
  correction requires a new alert (AC-1.5).
- **AC-16.6** A schedule-change alert (`category=SCHEDULE`) requires at least
  one old/new pair: `old_location`/`new_location` or `old_time`/`new_time`;
  both values are shown in detail and history. It derives
  `priority_source=SCHEDULE` and bypasses category mutes.
- **AC-16.7** Urgent and high-priority alerts still obey authorization,
  audience, snapshot, read and audit rules; urgency is not an authorization
  bypass.

### US-17 — Comments and moderation *(recipient / sender / comms_admin)*

> As a student, I want to see all the information about an alert and to be
> able to add a comment if I want to; as an administrator, I need to remove
> unwanted comments.

- **AC-17.1** Only an authenticated recipient of that alert may post a comment
  (HTTP 401/403 otherwise). The sender of the alert and `comms_admin` may read
  comments but do not need to be recipients.
- **AC-17.2** A comment body is plain text, trimmed, 1–500 characters; HTML is
  escaped and never rendered as markup. Invalid bodies return HTTP 400.
- **AC-17.3** Comments are visible to recipients of the alert, its sender, and
  `comms_admin`; unrelated users receive HTTP 403/404.
- **AC-17.4** The author may delete their own comment; `comms_admin` may remove
  any comment. Removal is a soft delete (`removed_at`, `removed_by`), hidden
  from recipients but retained for audit, and audit-logged (AC-7.3).
- **AC-17.5** Comments display author display name, body and server timestamp,
  oldest first; comment counts appear in the alert detail and sender report.
- **AC-17.6** Comments are disabled on alerts sent with `allow_comments=false`
  (comms_admin option); attempts return HTTP 409. Default is enabled.
- **AC-17.7** Comments never change delivery, read or acknowledgment state.

## Non-functional requirements

NFR numbering was compacted on 2026-11-02 to match the supplied Requirements
Document (NFR-1…NFR-20); five scope-driven entries were added as NFR-21…NFR-24.
Historical AI-log entries keep the old numbers and are marked as historical.

| ID | Requirement | Verification approach |
|----|-------------|----------------------|
| NFR-1 | **Server-side enforcement** of every role, audience and course/section boundary. | Unauthorized-request tests issued directly against the API (no Flutter client) |
| NFR-2 | **Zero paid/external services** at runtime; no outbound network calls for delivery. | Code review of channel adapters; test run with network-restricted settings |
| NFR-3 | **No contact data in logs**; log lines and audit details reference user IDs, not emails/phones. | Log-capture test asserting absence of address/phone patterns |
| NFR-4 | **Local deployment**: one documented command brings the backend up from a clean checkout; the Flutter app connects to it. | Fresh-clone setup rehearsal; `scripts/run_demo` |
| NFR-5 | **Auditability**: every state-changing operation (send, denial, ack, read, grant, comment moderation, reminder dispatch) is attributable and timestamped. | Audit-log tests tied to AC-7.3 |
| NFR-6 | **PSU review boundary**: repo documents that PSU security, privacy, accessibility and deployment review is required before real use. | README + docs statement (process, not test) |
| NFR-7 | **Critical-send latency**: a campus-wide `CRITICAL` send at seed scale (≈60 users × 3 channels) completes end-to-end — HTTP 201 plus all delivery rows persisted — within **2 s** on the reference machine. | Timed send test at seed scale; budget exceeded fails the test |
| NFR-8 | **Urgency presentation**: `CRITICAL` alerts stay in the active view until expiry or acknowledgment; urgent/exam/schedule-change alerts sort above normal traffic; lower severities never displace them. | API ordering tests + Flutter widget tests on the inbox order |
| NFR-9 | **Transactional send**: alert record, recipient snapshot, and all delivery records commit **atomically**; a mid-send failure rolls back the whole operation. | Forced-failure test asserting zero partial rows |
| NFR-10 | **State immutability**: delivery states are terminal and monotonic (`QUEUED → DELIVERED \| FAILED` only); acknowledgment timestamps, comments' moderation trail and audit entries are append-only. | State-machine tests attempting illegal transitions; no update/delete API paths for audit |
| NFR-11 | **Historical integrity**: directory, course, enrollment, section and user mutations after send never rewrite past alerts, snapshots, delivery records, acknowledgments or comments. | Test: mutate directory/enrollment post-send, re-fetch history, assert unchanged |
| NFR-12 | **Demo reset**: one management command (`manage.py reset_demo`) restores the database to a known seeded state (users, courses, enrollments, alerts) for demos and test runs. | Command runs green on a dirty database; subsequent seed assertions pass |
| NFR-13 | **Fail-fast configuration**: the system refuses to start with a dangerous or inconsistent configuration (e.g., a network-capable email backend, DEBUG with non-local hosts, missing encryption flag outside local mode) and names the offending setting. | Test invoking the config guard with bad settings; startup raises with a clear message |
| NFR-14 | **Mobile-phone-only UI**: the Flutter app targets 360–430 logical px widths, single-column, touch-first, targets ≥44 px. No desktop/web layout is built or maintained. | Flutter widget tests at 360/390/430 widths; layout-overflow checks; manual emulator pass |
| NFR-15 | **Channel extensibility**: adding a delivery channel requires a new `ChannelAdapter` implementation and an enum extension **only** — no modification to the alerts service. | Contract test against the adapter interface; code-review checklist |
| NFR-16 | **Test suite properties**: the full automated suite (Django + Flutter) runs offline in **< 60 s** on the reference machine; exceeding the budget is a defect. | Suite-timing measurement; documented baseline |
| NFR-17 | **License hygiene**: every runtime dependency (Python and Dart/Flutter) carries a permissive license (BSD/MIT/Apache-2.0); an inventory table lives in the README. | License inventory reviewed at each milestone |
| NFR-18 | **Secret scanning**: an automated check scans the repository for credential-like patterns (API keys, private keys, `.env` files) and fails if any are found. | Test executed with the suite; seeded canary secret must be caught |
| NFR-19 | **Bilingual interface (English + Arabic)**: all interface text — navigation, forms, buttons, status/severity/category labels, emails — is available in EN and AR; the user can switch at any time (persisted for the session). Flutter uses `intl`/ARB resources; dates, numbers and times format per the active language. Alert title/body stay as entered (A-20). | Missing-translation test; language-switch test; ARB key parity check |
| NFR-20 | **Arabic RTL correctness**: in Arabic the full Flutter UI renders right-to-left — mirrored navigation, rows and icons where directional, no half-mirrored screens — and remains usable at 360–430 px (NFR-14). Meaning is never carried by direction/colour alone. | `Directionality.rtl` widget tests; golden/screenshot review in AR; manual emulator pass |
| NFR-21 | **PSU-account-shaped authentication**: login uses synthetic accounts with PSU-style identifiers; credentials are stored only as Django password hashes. A real PSU SSO/OAuth integration is a documented adapter seam for handoff, not a v1 dependency. | Auth tests with synthetic accounts; review that no real directory/credential data exists; handoff note in README |
| NFR-22 | **Encryption in transit and at rest**: any non-localhost deployment must serve the API over HTTPS and store the database on an encrypted volume (or SQLCipher); the prototype runs localhost-only with synthetic data. A configuration guard refuses non-local hosts without HTTPS/encryption settings. | Settings-guard test; handoff checklist; documented boundary in [security note](design/security-privacy-accessibility.md) |
| NFR-23 | **One-minute delivery visibility**: every alert's simulated delivery rows reach a terminal state and are visible to the recipient within **60 s** of the server send timestamp, including course/exam/deadline alerts. The synchronous simulator meets this trivially; the test records elapsed time. | Timed delivery test at seed scale; assert maximum elapsed ≤60 s and all rows terminal |
| NFR-24 | **Concurrent use**: the backend serves at least 50 concurrent authenticated reads and 5 concurrent sends (seed scale, exam-period burst) without request errors or corrupted snapshots; SQLite runs in WAL mode. PostgreSQL is the documented handoff for higher write concurrency. | Concurrency test (threads/processes) against the API; WAL pragma test; documented ceiling |

## Traceability matrix

| Feature (team list / supplied docs) | User stories | Key acceptance criteria | NFRs |
|-------------------------------------|--------------|--------------------------|------|
| Authorization and Login | US-3, US-8, US-9 | 3.1–3.8, 8.1–8.4, 9.1–9.5 | NFR-1, NFR-21 |
| Notification Delivery | US-4 | 4.1–4.6 | NFR-2, NFR-7, NFR-9, NFR-15, NFR-23 |
| Data Protection | US-6, US-7, US-12 | 6.4, 7.3–7.4, 12.5 | NFR-1, NFR-3, NFR-6, NFR-22 |
| View Announcements | US-6 | 6.1–6.6 | NFR-8, NFR-14 |
| Filter Notifications | US-10 | 10.1–10.3 | NFR-1 |
| Categorize Notifications | US-11 | 11.1–11.5 | NFR-19 |
| Device Preferences | US-12 | 12.1–12.6 | NFR-19 |
| Read Status | US-13 | 13.1–13.4 | NFR-5 |
| Notification History | US-6 | 6.1–6.3, 6.6 | NFR-11 |
| Course / section alerts | US-2, US-3, US-14 | 2.1–2.5, 3.1–3.8, 14.1–14.7 | NFR-1, NFR-11 |
| Exam and deadline reminders | US-15 | 15.1–15.7 | NFR-8, NFR-23 |
| Urgent priority override | US-12, US-16 | 12.3, 16.1–16.7 | NFR-8, NFR-23 |
| Comments and moderation | US-17 | 17.1–17.7 | NFR-5, NFR-22 |
| Bilingual EN/AR | all UI | NFR-19/NFR-20 | NFR-19, NFR-20 |

## Traceability seed

| Requirement | Planned test home (Phase 4) |
|-------------|-----------------------------|
| US-1, US-2 | `alerts/tests/test_compose.py`, `test_audience.py` |
| US-3, US-8 | `alerts/tests/test_authorization.py` |
| US-4, US-23 | `alerts/tests/test_delivery.py` |
| US-5 | `alerts/tests/test_acknowledgment.py` |
| US-6 | `alerts/tests/test_history.py` |
| US-7 | `alerts/tests/test_reporting.py` |
| US-10…US-13 | `alerts/tests/test_preferences.py`, `test_filters.py`, `test_read_status.py` |
| US-14 | `alerts/tests/test_course_alerts.py` |
| US-15 | `alerts/tests/test_exams_deadlines.py` |
| US-16 | `alerts/tests/test_priority.py` |
| US-17 | `alerts/tests/test_comments.py` |
| NFR-1…NFR-6 | `core/tests/test_nfrs.py` + per-app misuse tests |
| NFR-14, NFR-19, NFR-20 | `mobile/test/` widget + layout tests |
| NFR-21…NFR-24 | `core/tests/test_deployment_boundary.py`, `test_concurrency.py` |

*Full criteria-to-test mapping is completed in Phase 4; this seed keeps
requirements and tests connected from the start.*
