import logging
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from triage.models import BaseTimestampedModel, BaseUserTrackedModel, WorkItemState

logger = logging.getLogger(__name__)


class Filter(BaseTimestampedModel, BaseUserTrackedModel):
    project = models.ForeignKey("Project", null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    definition = models.TextField()
    active = models.BooleanField(default=True)
    priority = models.PositiveSmallIntegerField(default=1000)

    def is_global(self):
        return self.project is None
