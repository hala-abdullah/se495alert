# ADR-001: Stack, Deployment Boundary, and UI Approach

*Phase 2 deliverable (T2.3). Status: accepted 2026-10-19; **superseded in part
2026-11-02** — the UI decision changed from server-rendered Django templates
to a Flutter mobile app, following `Design Doc.md` §1–3. The Flutter client
also takes over the bilingual/RTL work, so NFR-19/NFR-20 no longer depend on
Django templates. Feeds A-1…A-3, A-20, A-21.*

## Context

The prototype must run entirely on free, local tooling (no budget, no paid
services), be buildable and defensible by a small student team in eight weeks,
and demonstrate a credible alerting workflow to PSU evaluators. The supplied
`Design Doc.md` commits to a **Flutter mobile app + Django REST backend +
SQLite**, with delivery simulated in the backend and local synthetic accounts.
The course environment uses Python and Django; Flutter is the free mobile
framework available for the presentation tier.

## Decision

1. **Backend:** Python 3.14, Django 5.1, Django REST Framework 3.17 — one
   project, small apps (`accounts`, `directory`, `courses`, `alerts`,
   `audit`).
2. **Database:** SQLite (single file, git-ignored), standard Django ORM,
   WAL mode for concurrent reads/writes.
3. **Deployment boundary:** local only — `manage.py runserver`, no containers,
   no production WSGI, no external services at runtime. `scripts/run_demo`
   starts the backend and documents the `flutter run` step.
4. **UI:** a **Flutter mobile app**, **mobile-phone-only** (NFR-14): targets
   360–430 logical px, single-column, touch targets ≥44 px, no desktop/web
   layout and no separate admin dashboard. All admin screens live in the app.
   The Flutter client contains no authorization logic; it calls the same
   service layer the API exposes.
5. **Auth:** DRF token authentication over JSON; synthetic PSU-shaped demo
   accounts seeded by command. No real PSU SSO/OAuth in v1; the auth adapter
   is the handoff seam (NFR-21).
6. **Localization:** Flutter `intl`/ARB resources for EN/AR, `Directionality`
   for RTL, language switch persisted for the session (NFR-19/NFR-20).

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Server-rendered Django templates (the previous decision) | Viable and simpler for i18n, but the supplied design explicitly requires a Flutter mobile app and mobile-only product surface. Keeping templates would contradict the design source and duplicate the client work. Superseded 2026-11-02. |
| Flutter + separate web admin dashboard | The design's optional web admin panel doubles the surface, conflicts with mobile-only NFR-14, and adds a second i18n/RTL implementation. Admin screens fit in the app. |
| Node/Express + React Native | Two runtimes; Django already gives us auth, ORM, migrations and the course starter. Flutter is the specified client. |
| Flask/FastAPI + SQLAlchemy | Lighter, but we would rebuild auth, migrations and admin tooling that Django ships. |
| PostgreSQL | Realistic for production, but install/serve overhead for tens of rows; SQLite is the course default and trivially migratable. PostgreSQL is the concurrency handoff (NFR-24). |
| Firebase/APNs for real push and PSU SSO | Explicitly rejected by C-1/C-2 (no budget, no real gateway) and C-3/C-5 (synthetic data only). The `ChannelAdapter` and auth adapter seams keep them replaceable. |
| Real HTTPS reverse proxy + Docker | Correct for deployment, out of boundary for "local deployment is sufficient"; documented as PSU handoff work. |

## Consequences accepted

- **Two toolchains:** Python/Django and Flutter/Dart must both be installed;
  this is recorded as risk R12 and the README setup covers both. Widget tests
  do not need a device (they run in the Flutter test harness).
- **SQLite** limits concurrent writers — acceptable at prototype scale
  (NFR-24 targets 5 concurrent sends); WAL mode is enabled, and PostgreSQL is
  the documented handoff.
- **Dev SECRET_KEY and DEBUG** live in the repo — acceptable *only* because the
  deployment boundary is local (flagged in
  [security-privacy-accessibility](../security-privacy-accessibility.md);
  NFR-13/NFR-22 guards refuse non-local configurations without HTTPS/encrypted
  storage settings).
- **Mobile-only (NFR-14):** no desktop layout or responsive breakpoints are
  maintained; evaluators use a phone-sized emulator. Officers composing long
  alerts on a phone is the assumed (and more stressful) case, which suits the
  "send quickly under pressure" brief.
- **PSU-shaped synthetic auth** is simpler than OAuth/SSO — PSU identity
  integration is explicitly deferred to the pre-deployment review (NFR-6,
  NFR-21).
- **No web admin dashboard:** the Django admin site remains a developer tool
  only; comms_admin operations are exposed through the app and API.
- The team must keep the service layer honest: if views start touching alert
  ORM tables directly, the single-choke-point property in
  [architecture.md](../architecture.md) dies silently. Enforced by code review
  + independent API-level authorization tests (R4).
