"""Synthetic directory used for audience targeting (US-2).

These tables hold invented organizations only. No real PSU directory records
may ever be imported (NFR-3, C-3/C-5).
"""

from django.conf import settings
from django.db import models


class Department(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Building(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Group(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="directory_groups",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"
