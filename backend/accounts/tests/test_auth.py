from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import Profile, RoleFamily
from audit.models import AuditLogEntry

User = get_user_model()

PASSWORD = "correct-horse-battery"

FAST_HASHER = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student = self._make_user(
            "s123456",
            campus_role=Profile.CampusRole.STUDENT,
            system_role=Profile.SystemRole.RECIPIENT,
        )
        self.faculty = self._make_user(
            "f900001",
            campus_role=Profile.CampusRole.FACULTY,
            system_role=Profile.SystemRole.RECIPIENT,
        )
        self.officer = self._make_user(
            "o700001",
            system_role=Profile.SystemRole.OFFICER,
        )
        self.comms_admin = self._make_user(
            "a800001",
            system_role=Profile.SystemRole.COMMS_ADMIN,
        )

    @staticmethod
    def _make_user(username, *, campus_role=Profile.CampusRole.STUDENT, system_role=Profile.SystemRole.RECIPIENT):
        user = User.objects.create_user(
            username=username,
            password=PASSWORD,
            first_name="Demo",
            last_name="User",
        )
        Profile.objects.create(
            user=user,
            campus_role=campus_role,
            system_role=system_role,
            student_id=username,
            synthetic_email=f"{username}@example.edu",
            synthetic_phone="+00000000000",
        )
        return user

    def _login(self, username, password=PASSWORD):
        return self.client.post(
            reverse("accounts:login"),
            {"username": username, "password": password},
            format="json",
        )


class LoginTests(AuthTestCase):
    def test_valid_login_returns_token_and_identity(self):
        response = self._login("s123456")
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["role_family"], RoleFamily.STUDENT)
        self.assertEqual(response.data["user"]["system_role"], Profile.SystemRole.RECIPIENT)
        self.assertTrue(Token.objects.filter(user=self.student).exists())
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action=AuditLogEntry.Action.LOGIN_SUCCEEDED, actor=self.student
            ).exists()
        )

    def test_role_family_is_derived_for_each_account(self):
        cases = {
            "s123456": RoleFamily.STUDENT,
            "f900001": RoleFamily.FACULTY,
            "o700001": RoleFamily.ADMIN,
            "a800001": RoleFamily.ADMIN,
        }
        for username, family in cases.items():
            with self.subTest(username=username):
                response = self._login(username)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["user"]["role_family"], family)

    def test_bad_password_and_unknown_user_share_one_generic_error(self):
        bad_password = self._login("s123456", "wrong-password")
        unknown = self._login("nobody", "wrong-password")
        self.assertEqual(bad_password.status_code, 401)
        self.assertEqual(unknown.status_code, 401)
        self.assertEqual(bad_password.data, unknown.data)
        self.assertNotIn("username", bad_password.data)
        self.assertNotIn("password", bad_password.data)

    def test_failed_login_is_audited_without_contact_data(self):
        self._login("s123456", "wrong-password")
        entry = AuditLogEntry.objects.get(action=AuditLogEntry.Action.LOGIN_FAILED)
        self.assertIsNone(entry.actor)
        self.assertEqual(entry.actor_label, "s123456")
        self.assertEqual(entry.detail.get("reason"), "invalid_credentials")
        self.assertNotIn("@", str(entry.detail))

    def test_inactive_user_cannot_log_in(self):
        self.student.is_active = False
        self.student.save(update_fields=["is_active"])
        response = self._login("s123456")
        self.assertEqual(response.status_code, 401)

    def test_login_requires_both_fields(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "s123456"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data["fields"])

    def test_login_is_the_only_anonymous_endpoint(self):
        response = self.client.get(reverse("accounts:me"))
        self.assertIn(response.status_code, (401, 403))
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action=AuditLogEntry.Action.REQUEST_DENIED
            ).exists()
        )


class IdentityTests(AuthTestCase):
    def _authenticated(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return self.client.get(reverse("accounts:me"))

    def test_me_returns_the_authenticated_user_only(self):
        response = self._authenticated(self.student)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "s123456")
        self.assertNotIn("password", response.data)

    def test_student_permissions_are_read_only(self):
        response = self._authenticated(self.student)
        permissions = response.data["permissions"]
        self.assertFalse(permissions["can_send"])
        self.assertFalse(permissions["can_send_critical"])
        self.assertFalse(permissions["can_manage_senders"])
        self.assertEqual(permissions["audience_types"], [])

    def test_faculty_can_send_but_not_critical(self):
        response = self._authenticated(self.faculty)
        permissions = response.data["permissions"]
        self.assertTrue(permissions["can_send"])
        self.assertFalse(permissions["can_send_critical"])
        self.assertEqual(permissions["audience_types"], ["course", "section"])

    def test_officer_is_admin_family_but_not_comms_admin(self):
        response = self._authenticated(self.officer)
        self.assertEqual(response.data["role_family"], RoleFamily.ADMIN)
        permissions = response.data["permissions"]
        self.assertTrue(permissions["can_send_critical"])
        self.assertFalse(permissions["can_manage_senders"])
        self.assertFalse(permissions["can_moderate_comments"])

    def test_comms_admin_has_management_permissions(self):
        response = self._authenticated(self.comms_admin)
        permissions = response.data["permissions"]
        self.assertTrue(permissions["can_manage_senders"])
        self.assertTrue(permissions["can_manage_categories"])
        self.assertTrue(permissions["can_view_system_reports"])
        self.assertIn("everyone", permissions["audience_types"])

    def test_missing_profile_never_grants_elevated_rights(self):
        bare = User.objects.create_user(username="bare", password=PASSWORD)
        response = self._authenticated(bare)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role_family"], RoleFamily.STUDENT)
        self.assertFalse(response.data["permissions"]["can_send"])


class LogoutTests(AuthTestCase):
    def test_logout_invalidates_the_token_and_is_audited(self):
        token = Token.objects.create(user=self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Token.objects.filter(user=self.student).exists())
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action=AuditLogEntry.Action.LOGOUT, actor=self.student
            ).exists()
        )

        reused = self.client.get(reverse("accounts:me"))
        self.assertIn(reused.status_code, (401, 403))


class RoleGateTests(AuthTestCase):
    def test_student_is_refused_an_admin_gate_and_the_rejection_is_audited(self):
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework.response import Response
        from rest_framework.views import APIView

        from core.permissions import IsCommsAdmin

        class AdminOnlyView(APIView):
            permission_classes = [IsCommsAdmin]

            def get(self, request):
                return Response({"ok": True})

        factory = APIRequestFactory()
        request = factory.get("/api/admin/")
        force_authenticate(request, user=self.student)
        response = AdminOnlyView.as_view()(request)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action=AuditLogEntry.Action.REQUEST_DENIED
            ).exists()
        )
