import logging
import uuid

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _

from triage.models import Note, Tool, WorkItemState
from triage.util.general import modify_purl

logger = logging.getLogger(__name__)


class ToolDefect(models.Model):
    """
    A tool defect is a defect that is filed against a tool.
    """

    tool = models.ForeignKey(Tool, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    title = models.CharField(max_length=1024)
    finding = models.ManyToManyField("Finding")
    state = models.CharField(choices=WorkItemState.choices, max_length=2, default=WorkItemState.NEW)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.ManyToManyField(Note)

    def __str__(self):
        return self.title
