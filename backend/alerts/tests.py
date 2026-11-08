from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class SmokeTests(SimpleTestCase):
    """Skeleton checks only — behavior arrives with Phase 3 tasks (see docs/task-plan.md)."""

    def test_health_endpoint_returns_ok(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_backend_never_leaves_the_process(self):
        from django.core import mail

        mail.send_mail("subj", "body", "from@example.edu", ["to@example.edu"])
        self.assertEqual(len(mail.outbox), 1)
