from django.test import TestCase

from audit.models import AuditLogEntry
from audit.writer import log


class AuditAppendOnlyTests(TestCase):
    def test_entries_can_be_created(self):
        entry = log(
            action=AuditLogEntry.Action.REQUEST_DENIED,
            actor_label="anonymous",
            object_type="endpoint",
            object_id="/api/alerts/",
            detail={"status": 403},
        )
        self.assertIsNotNone(entry.pk)

    def test_entries_cannot_be_updated(self):
        entry = log(action=AuditLogEntry.Action.LOGOUT, actor_label="demo")
        entry.object_id = "changed"
        with self.assertRaises(ValueError):
            entry.save()
