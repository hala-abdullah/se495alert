# PSU Alerts & Notifications — SE495 Prototype

Campus alerts and notifications prototype for Prince Sultan University
(course project for SE495).

> **Prototype only.** Synthetic data, simulated delivery, local deployment.
> No real student, faculty or staff information is stored in this repository.

## Repository layout

```
se495alert/
├── frontend/        Flutter app (runs in Chrome)
│   ├── lib/
│   │   ├── main.dart            app entry: theme, English/Arabic, RTL
│   │   ├── data.dart            fake accounts and alerts
│   │   ├── widgets.dart         shared top bar, headings, ✓ button
│   │   ├── translations.dart    English → Arabic text
│   │   └── screens/             login, student, alert, staff, new alert, preferences
│   ├── test/widget_test.dart    widget tests UI-1 … UI-10
│   └── web/                     web (Chrome) platform files
└── backend/         Django REST API + SQLite
    ├── psu_alerts/              Django project settings and root URLs
    ├── accounts/                login, logout, profiles, sender scopes
    ├── alerts/                  alert authorization and audience services
    ├── audit/                   audit log
    ├── core/                    shared permissions and errors
    ├── courses/ directory/      courses, sections, departments, buildings
    └── docs/                    requirements, design, ADRs, AI-use log
```

## Run the frontend (Flutter, Chrome)

```bash
cd frontend
flutter pub get
flutter run -d chrome
flutter test
```

Test accounts (password `1234`): `student@psu.test` (Student tab),
`faculty@psu.test` and `admin@psu.test` (Faculty tab).

## Run the backend (Django)

Needs Python 3.10 or newer (`brew install python@3.13` on macOS).

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py test
python manage.py runserver      # http://localhost:8000/api/health/
```

## Team

| Student | Area |
|---------|------|
| Student 1 | Backend structure, authentication, role/scope authorization, backend tests |
| Student 2 | Flutter screens, REST integration, widget and workflow tests |
| Student 3 | Simulated delivery, acknowledgment storage, reporting, integration tests, deployment |

## Current status

- Frontend uses fake data in `frontend/lib/data.dart`; it is not yet connected to the backend.
- Backend has health, login/logout/me, role and scope authorization, and audit logging.
  Alert, delivery, acknowledgment, comment and preference endpoints are still to be added.
