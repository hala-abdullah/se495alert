# ADR-002: Delivery Simulation Strategy

*Phase 2 deliverable (T2.4). Status: accepted 2026-10-19; revised 2026-10-20
(per-recipient channel preferences, US-12) and 2026-11-02 (category opt-outs,
urgent/exam bypass, one-minute SLA, reminder runner). Feeds US-4, US-12,
US-15, US-16, AC-4.1–4.6, NFR-2/NFR-7/NFR-15/NFR-23.*

## Context

Stakeholders want to see whether alerts actually reached people, but the
brief forbids real SMS/push gateways and any paid service. The prototype
must still (a) demonstrate a believable multi-channel flow in the demo,
(b) make the FAILED path deterministically testable, and (c) leave PSU a
clear seam where real gateways would plug in later. The supplied Requirements
Document adds a "push within 1 minute" expectation and mute-bypass rules for
exam/urgent alerts, both of which must be expressed without a real push
service.

## Decision

A **channel adapter interface** with three v1 implementations, driven by a
synchronous in-request dispatcher:

```
ChannelAdapter.send(alert, recipient, payload) -> DeliveryResult(status, reason)
├── EmailAdapter  — real Django email stack; EMAIL_BACKEND=console (dev) prints RFC-822 mail
├── SmsAdapter    — appends SimulatedOutboxMessage row; fails if synthetic_phone is null
└── PushAdapter   — appends SimulatedOutboxMessage row with a JSON payload
                    (sound, vibration_pattern, bypass_mute, priority_source)
```

- Every recipient × effective-channel pair gets a `DeliveryRecord` starting
  `QUEUED` (AC-4.1); the dispatcher immediately transitions it to `DELIVERED`
  or `FAILED` (AC-4.2).
- Effective channels = sender-selected ∩ recipient-enabled, minus category
  opt-outs. **Forced channels:** `CRITICAL`, `is_urgent`, `priority_source`
  `EXAM`/`DEADLINE`/`SCHEDULE` always produce a portal row and a simulated
  `PUSH` record, even if the recipient disabled push or opted out of the
  category (AC-12.3, AC-15.2, AC-16.2). The record is marked `forced=true`.
- Failure injection is **deterministic and data-driven**: `SMS` to a
  recipient without `synthetic_phone` fails with reason
  `no_mobile_on_profile` (AC-4.4). No randomness — tests assert exact counts.
- Email uses Django's real mail stack so the email-shaped output (headers,
  body, recipient) is authentic; only the transport is stubbed. SMS/push are
  visible in demos through the outbox table and the dev-only outbox endpoint.
- No outbound network call exists anywhere in the send path (NFR-2); a
  regression test enforces the console/locmem backends in test settings.
- **One-minute SLA (NFR-23):** the dispatcher records `attempted_at` and
  `completed_at` per row; a timed test asserts all rows are terminal and
  visible within 60 s. Synchronous dispatch makes this effectively immediate,
  but the measurement stays so the requirement is demonstrated rather than
  assumed.
- **Reminders:** deadline reminders are dispatched by
  `manage.py send_due_reminders`, not by a broker or external cron. A unique
  dispatch marker per (alert, recipient) makes repeated runs idempotent
  (AC-15.4). The same adapter path is used.

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| One `simulate_delivery()` that flips random statuses | Fast to write, but demos become unpredictable, tests assert nothing meaningful, and PSU cannot inspect *what* was sent — exactly the "we're never sure who saw it" complaint this project exists to fix. |
| External local gateways (MailHog, Mailpit, a fake SMS daemon) | Genuinely useful tools, but they are outside services to install and explain at every demo; the brief prefers zero outside dependencies. Console email gives inspectability with zero install. |
| Real gateways (Twilio, FCM/APNs, university SMTP) | Explicitly out of scope and budget; storing any real destination data would violate NFR-1. The design's §6 Firebase/APNs reference is a handoff item, not v1. |
| Celery/RQ async queue from day one | Right for production volume; wrong for a prototype sending to ~60 synthetic users. A queue adds broker ops, failure modes, and demo complexity. The DeliveryRecord state machine already supports async later (see consequences). |
| Real device push to demonstrate sound/vibration | Requires FCM/APNs keys, a real device, and an external service. The simulated payload carries the same `sound`/`vibration_pattern` fields so the Flutter client can render/test the distinction locally. |

## Consequences accepted

- **SMS/push realism is a database table plus a Flutter payload, not an actual
  phone notification.** The demo walks evaluators through the outbox view and
  the app's urgent presentation; we accept that framing cost in exchange for
  zero dependencies.
- **Synchronous dispatch inside the request** couples send latency to the
  simulated work. Fine for ~60 recipients; at real scale the same dispatcher
  moves behind a task queue with no schema change (states and records already
  model time and failure).
- **The "1 minute" requirement is a simulated SLA.** It is honest and
  testable; real push delivery time is a PSU handoff metric that depends on
  the chosen gateway and carrier. Recorded in Q16.
- **The adapter interface is a promise to PSU**: replacing `SmsAdapter`
  internals with a real gateway must not require touching the alerts service.
  Adapters receive only (alert, recipient, payload) and return a status.
- **Deterministic failures can look artificial** (every phone-less recipient
  fails SMS). That is preferred over randomness for testability; the seed
  data marks a realistic minority as phone-less (~15%) so the failure
  percentage in demos looks plausible.
- If PSU later requires delivery receipts distinct from "read" or
  "acknowledged", the adapter result vocabulary grows (`DELIVERED` stays
  transport-level; ack remains an explicit user action — R10).
