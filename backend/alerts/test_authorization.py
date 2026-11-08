from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from accounts.models import OfficerScope, Profile
from alerts.constants import AudienceType, Severity
from alerts.services.authorization import SendDenied, SendRequest, authorize_send
from audit.models import AuditLogEntry
from courses.models import Course, FacultyAssignment, Section
from directory.models import Building, Department, Group

User = get_user_model()
PASSWORD = "correct-horse-battery"


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)
class AuthorizationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.eng = Department.objects.create(code="ENG", name="Engineering")
        cls.med = Department.objects.create(code="MED", name="Medicine")
        cls.science = Building.objects.create(code="SCI", name="Science Hall")
        cls.library = Building.objects.create(code="LIB", name="Library")
        cls.safety = Group.objects.create(code="SAFETY", name="Safety Team")

        cls.cs101 = Course.objects.create(code="CS101", title="Intro CS", department=cls.eng)
        cls.med201 = Course.objects.create(code="MED201", title="Anatomy", department=cls.med)
        cls.cs101_01 = Section.objects.create(course=cls.cs101, code="01", term="2026F")
        cls.cs101_02 = Section.objects.create(course=cls.cs101, code="02", term="2026F")
        cls.med201_01 = Section.objects.create(course=cls.med201, code="01", term="2026F")

        cls.student = cls._user("s1", campus_role=Profile.CampusRole.STUDENT)
        cls.faculty = cls._user("f1", campus_role=Profile.CampusRole.FACULTY)
        cls.other_faculty = cls._user("f2", campus_role=Profile.CampusRole.FACULTY)
        cls.officer = cls._user("o1", system_role=Profile.SystemRole.OFFICER)
        cls.campus_officer = cls._user("o2", system_role=Profile.SystemRole.OFFICER)
        cls.comms_admin = cls._user("a1", system_role=Profile.SystemRole.COMMS_ADMIN)

        FacultyAssignment.objects.create(
            user=cls.faculty, course=cls.cs101, section=None
        )
        FacultyAssignment.objects.create(
            user=cls.other_faculty, course=cls.cs101, section=cls.cs101_02
        )
        OfficerScope.objects.create(
            user=cls.officer,
            scope_type=OfficerScope.ScopeType.DEPARTMENT,
            department=cls.eng,
        )
        OfficerScope.objects.create(
            user=cls.officer,
            scope_type=OfficerScope.ScopeType.BUILDING,
            building=cls.library,
        )
        OfficerScope.objects.create(
            user=cls.campus_officer,
            scope_type=OfficerScope.ScopeType.CAMPUS_WIDE,
        )

    @classmethod
    def _user(cls, username, *, campus_role=Profile.CampusRole.STUDENT, system_role=Profile.SystemRole.RECIPIENT):
        user = User.objects.create_user(username=username, password=PASSWORD)
        Profile.objects.create(
            user=user,
            campus_role=campus_role,
            system_role=system_role,
            department=cls.eng,
            building=cls.science,
        )
        return user

    def assertAllowed(self, actor, **kwargs):
        authorize_send(actor, SendRequest(**kwargs))
        self.assertFalse(
            AuditLogEntry.objects.filter(
                action=AuditLogEntry.Action.SEND_DENIED
            ).exists()
        )

    def assertDenied(self, actor, reason, **kwargs):
        with self.assertRaises(SendDenied) as ctx:
            authorize_send(actor, SendRequest(**kwargs))
        self.assertEqual(ctx.exception.reason, reason)
        entry = AuditLogEntry.objects.filter(
            action=AuditLogEntry.Action.SEND_DENIED
        ).latest("id")
        self.assertEqual(entry.detail.get("reason"), reason)
        return entry


class RoleRuleTests(AuthorizationTestCase):
    def test_student_can_never_send(self):
        entry = self.assertDenied(
            self.student,
            "role_cannot_send",
            audience_type=AudienceType.COURSE,
            severity=Severity.INFORMATIONAL,
            course=self.cs101,
        )
        self.assertEqual(entry.actor, self.student)

    def test_unauthenticated_send_is_denied(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertDenied(
            AnonymousUser(),
            "unauthenticated",
            audience_type=AudienceType.COURSE,
            severity=Severity.ADVISORY,
            course=self.cs101,
        )

    def test_faculty_can_send_to_own_course(self):
        self.assertAllowed(
            self.faculty,
            audience_type=AudienceType.COURSE,
            severity=Severity.ADVISORY,
            course=self.cs101,
        )

    def test_faculty_can_send_urgent_to_own_course(self):
        self.assertAllowed(
            self.faculty,
            audience_type=AudienceType.COURSE,
            severity=Severity.INFORMATIONAL,
            is_urgent=True,
            course=self.cs101,
        )

    def test_faculty_cannot_send_critical(self):
        self.assertDenied(
            self.faculty,
            "faculty_severity",
            audience_type=AudienceType.COURSE,
            severity=Severity.CRITICAL,
            course=self.cs101,
        )

    def test_faculty_cannot_send_to_unassigned_course(self):
        self.assertDenied(
            self.faculty,
            "faculty_course_grant_required",
            audience_type=AudienceType.COURSE,
            severity=Severity.ADVISORY,
            course=self.med201,
        )

    def test_faculty_cannot_use_campus_audience(self):
        self.assertDenied(
            self.faculty,
            "faculty_audience",
            audience_type=AudienceType.EVERYONE,
            severity=Severity.INFORMATIONAL,
        )

    def test_section_grant_allows_that_section_but_not_the_whole_course(self):
        self.assertAllowed(
            self.other_faculty,
            audience_type=AudienceType.SECTION,
            severity=Severity.ADVISORY,
            section=self.cs101_02,
        )
        self.assertDenied(
            self.other_faculty,
            "faculty_course_grant_required",
            audience_type=AudienceType.COURSE,
            severity=Severity.ADVISORY,
            course=self.cs101,
        )

    def test_whole_course_grant_covers_any_section_of_that_course(self):
        self.assertAllowed(
            self.faculty,
            audience_type=AudienceType.SECTION,
            severity=Severity.ADVISORY,
            section=self.cs101_01,
        )
        self.assertDenied(
            self.faculty,
            "faculty_course_grant_required",
            audience_type=AudienceType.SECTION,
            severity=Severity.ADVISORY,
            section=self.med201_01,
        )

    def test_section_must_belong_to_the_named_course(self):
        self.assertDenied(
            self.faculty,
            "invalid_audience",
            audience_type=AudienceType.SECTION,
            severity=Severity.ADVISORY,
            course=self.med201,
            section=self.cs101_01,
        )


class OfficerScopeTests(AuthorizationTestCase):
    def test_officer_may_target_their_department(self):
        self.assertAllowed(
            self.officer,
            audience_type=AudienceType.DEPARTMENT,
            severity=Severity.ADVISORY,
            department=self.eng,
        )

    def test_officer_may_not_target_another_department(self):
        self.assertDenied(
            self.officer,
            "officer_audience_out_of_scope",
            audience_type=AudienceType.DEPARTMENT,
            severity=Severity.ADVISORY,
            department=self.med,
        )

    def test_department_scope_covers_courses_in_that_department(self):
        self.assertAllowed(
            self.officer,
            audience_type=AudienceType.COURSE,
            severity=Severity.CRITICAL,
            course=self.cs101,
        )
        self.assertDenied(
            self.officer,
            "officer_audience_out_of_scope",
            audience_type=AudienceType.COURSE,
            severity=Severity.CRITICAL,
            course=self.med201,
        )

    def test_building_scope_covers_only_that_building(self):
        self.assertAllowed(
            self.officer,
            audience_type=AudienceType.BUILDING,
            severity=Severity.ADVISORY,
            building=self.library,
        )
        self.assertDenied(
            self.officer,
            "officer_audience_out_of_scope",
            audience_type=AudienceType.BUILDING,
            severity=Severity.ADVISORY,
            building=self.science,
        )

    def test_non_campus_officer_cannot_target_everyone(self):
        self.assertDenied(
            self.officer,
            "officer_audience_out_of_scope",
            audience_type=AudienceType.EVERYONE,
            severity=Severity.CRITICAL,
        )

    def test_campus_scope_covers_every_selector(self):
        self.assertAllowed(
            self.campus_officer,
            audience_type=AudienceType.EVERYONE,
            severity=Severity.CRITICAL,
        )
        self.assertAllowed(
            self.campus_officer,
            audience_type=AudienceType.ROLE,
            role="STUDENT",
            severity=Severity.ADVISORY,
        )
        self.assertAllowed(
            self.campus_officer,
            audience_type=AudienceType.COURSE,
            severity=Severity.CRITICAL,
            course=self.med201,
        )

    def test_comms_admin_ignores_scopes(self):
        self.assertAllowed(
            self.comms_admin,
            audience_type=AudienceType.EVERYONE,
            severity=Severity.CRITICAL,
        )
        self.assertAllowed(
            self.comms_admin,
            audience_type=AudienceType.GROUP,
            severity=Severity.ADVISORY,
            group=self.safety,
        )

    def test_missing_target_is_invalid(self):
        self.assertDenied(
            self.campus_officer,
            "invalid_audience",
            audience_type=AudienceType.DEPARTMENT,
            severity=Severity.ADVISORY,
        )


class AuthorizationAuditTests(AuthorizationTestCase):
    def test_denial_audit_contains_ids_not_contact_data(self):
        entry = self.assertDenied(
            self.officer,
            "officer_audience_out_of_scope",
            audience_type=AudienceType.DEPARTMENT,
            severity=Severity.ADVISORY,
            department=self.med,
        )
        self.assertEqual(entry.detail["target_ids"]["department"], self.med.pk)
        self.assertNotIn("@", str(entry.detail))

    def test_audit_can_be_disabled_for_pure_checks(self):
        with self.assertRaises(SendDenied):
            authorize_send(
                self.student,
                SendRequest(
                    audience_type=AudienceType.EVERYONE,
                    severity=Severity.INFORMATIONAL,
                ),
                audit=False,
            )
        self.assertFalse(
            AuditLogEntry.objects.filter(
                action=AuditLogEntry.Action.SEND_DENIED
            ).exists()
        )
