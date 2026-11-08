# PSU Alerts — Flutter frontend

Flutter client for the PSU Alerts & Notifications prototype (Student 2).
Runs in Chrome and uses fake data from `lib/data.dart`.

## Run

```bash
flutter pub get
flutter run -d chrome     # r = reload, R = restart, q = quit
flutter test              # widget tests UI-1 … UI-10
```

## Test accounts (password `1234`)

| Email | Login tab | Role | Home screen |
|-------|-----------|------|-------------|
| student@psu.test | Student | Student | Recent Alert + Past Alerts |
| faculty@psu.test | Faculty | Faculty | New Alert + Sent Alerts (Medium/Low) |
| admin@psu.test | Faculty | Admin | New Alert + Sent Alerts (High/Medium/Low) |

## Files

| File | Purpose |
|------|---------|
| `lib/main.dart` | App entry: title, theme, English/Arabic and right-to-left |
| `lib/data.dart` | Fake accounts, `Alert` class, fake alerts |
| `lib/widgets.dart` | Shared top bar (en/ar button), headings, ✓ acknowledge button |
| `lib/translations.dart` | English → Arabic text and the `tr()` helper |
| `lib/screens/login_page.dart` | Login with Student / Faculty tabs |
| `lib/screens/student_home.dart` | Recent Alert, Past Alerts, ✓ and comments |
| `lib/screens/alert_page.dart` | Alert details, ✓, comments |
| `lib/screens/preferences_page.dart` | Email / SMS / Push switches |
| `lib/screens/staff_home.dart` | + New Alert, Sent Alerts with views |
| `lib/screens/create_alert.dart` | Title, message, severity, course, section, send |
| `test/widget_test.dart` | Widget tests UI-1 … UI-10 |
