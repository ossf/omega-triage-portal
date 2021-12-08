import logging
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from triage.models import BaseTimestampedModel, BaseUserTrackedModel, WorkItemState

logger = logging.getLogger(__name__)


class Filter(BaseTimestampedModel, BaseUserTrackedModel):
    """
    Represents a filter that is automatically applied to a Finding.

    The purpose of this is to allow users to improve the quality of findings in a
    programmatic way.

    All filters are run automatically when a Finding is created or modified.
    If a filter is modified, it will be re-run on all Findings.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    condition = models.TextField(null=True, blank=True)
    action = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    priority = models.PositiveSmallIntegerField(default=1000)
