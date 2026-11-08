"""Shared vocabulary for the alerts domain.

Severity and category stay config-driven at the API layer; these enums define
the values the service layer accepts (AC-1.3, AC-11.1).
"""

from django.db import models


class Severity(models.TextChoices):
    CRITICAL = "CRITICAL", "Critical"
    ADVISORY = "ADVISORY", "Advisory"
    INFORMATIONAL = "INFORMATIONAL", "Informational"


class AudienceType(models.TextChoices):
    EVERYONE = "everyone", "Everyone"
    ROLE = "role", "Role"
    DEPARTMENT = "department", "Department"
    BUILDING = "building", "Building"
    GROUP = "group", "Group"
    COURSE = "course", "Course"
    SECTION = "section", "Section"


class PrioritySource(models.TextChoices):
    NORMAL = "NORMAL", "Normal"
    EXAM = "EXAM", "Exam"
    DEADLINE = "DEADLINE", "Deadline"
    SCHEDULE = "SCHEDULE", "Schedule"
    URGENT = "URGENT", "Urgent"
