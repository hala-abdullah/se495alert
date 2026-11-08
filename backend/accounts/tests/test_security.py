"""Authentication and session security tests (P0 additions).

Complements ``accounts/tests/test_auth.py`` with token handling, mass-assignment
resistance, password storage, and the minimal anonymous surface.
"""

from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import Profile, RoleFamily
from audit.models import AuditLogEntry

User = get_user_model()
PASSWORD = "correct-horse-battery"


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)
class AuthSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username="sec.auth.student",
            password=PASSWORD,
            first_name="Sec",
            last_name="Student",
        )
        Profile.objects.create(
            user=cls.student,
            campus_role=Profile.CampusRole.STUDENT,
            system_role=Profile.SystemRole.RECIPIENT,
            student_id="sec.auth.student",
            synthetic_email="sec.auth.student@example.edu",
        )

    def setUp(self):
        self.client = APIClient()

    def _login(self, **extra):
        payload = {"username": self.student.username, "password": PASSWORD, **extra}
        return self.client.post(reverse("accounts:login"), payload, format="json")

    def test_invalid_token_is_rejected_and_audited(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token not-a-real-token")
        response = self.client.get(reverse("accounts:me"))

        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action=AuditLogEntry.Action.REQUEST_DENIED
            ).exists()
        )

    def test_logout_then_login_issues_a_new_token(self):
        first = self._login()
        first_token = first.data["token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {first_token}")
        self.assertEqual(
            self.client.post(reverse("accounts:logout")).status_code, 204
        )

        second = self._login()
        second_token = second.data["token"]
        self.assertNotEqual(second_token, first_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {first_token}")
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 401)

    def test_login_ignores_privilege_fields_in_the_payload(self):
        response = self._login(
            system_role="COMMS_ADMIN",
            role_family="ADMIN",
            is_staff=True,
            is_superuser=True,
            permissions={"can_send_critical": True, "audience_types": ["everyone"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["role_family"], RoleFamily.STUDENT)
        self.assertEqual(
            response.data["user"]["system_role"], Profile.SystemRole.RECIPIENT
        )
        self.assertFalse(response.data["user"]["permissions"]["can_send"])

        self.student.refresh_from_db()
        self.assertFalse(self.student.is_staff)
        self.assertFalse(self.student.is_superuser)
        self.assertEqual(
            Profile.objects.get(user=self.student).system_role,
            Profile.SystemRole.RECIPIENT,
        )

    def test_password_is_hashed_and_never_echoed(self):
        self.assertTrue(self.student.check_password(PASSWORD))
        self.assertNotEqual(self.student.password, PASSWORD)

        response = self._login()
        body = json.dumps(dict(response.data))
        self.assertNotIn(PASSWORD, body)

        for entry in AuditLogEntry.objects.all():
            self.assertNotIn(PASSWORD, str(entry.detail))
            self.assertNotIn(PASSWORD, entry.actor_label)

    def test_inactive_user_cannot_log_in_and_gets_no_token(self):
        self.student.is_active = False
        self.student.save(update_fields=["is_active"])

        response = self._login()

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Token.objects.filter(user=self.student).exists())
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action=AuditLogEntry.Action.LOGIN_FAILED,
                actor_label=self.student.username,
            ).exists()
        )

    def test_health_endpoint_is_anonymous_and_minimal(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body, {"status": "ok"})
        self.assertEqual(set(body), {"status"})

    def test_health_endpoint_rejects_non_get_methods(self):
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse("health"))
                self.assertEqual(response.status_code, 405)
