import logging
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from triage.models import BaseTimestampedModel, BaseUserTrackedModel

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

    def __str__(self):
        return self.title

    def clean(self):
        """
        Validate that the condition and action are valid Python code.
        """
        try:
            condition_str = "def condition(finding):\n" + "\n".join(
                ["  " + line for line in self.condition.splitlines()]
            )
            compile(condition_str, "validation", "exec")
        except Exception as msg:
            raise ValidationError(_("Condition is not valid Python code."))

        try:
            action_str = "def action(finding):\n" + "\n".join(
                ["  " + line for line in self.action.splitlines()]
            )
            compile(action_str, "validation", "exec")
        except Exception as msg:
            raise ValidationError(_("Action is not valid Python code."))

        if not self.title:
            raise ValidationError(_("Title is required."))

        if self.priority < 0 or self.priority > 1000:
            raise ValidationError(_("Priority must be between 0 and 1000."))

    def execute(self):
        """
        Execute the filter's condition and action.
        """
        from triage.models import Finding

        try:
            condition_str = "def condition(finding):\n" + "\n".join(
                ["  " + line for line in self.condition.splitlines()]
            )
            print(condition_str)
            exec(condition_str)

            action_str = "def action(finding):\n" + "\n".join(
                ["  " + line for line in self.action.splitlines()]
            )
            exec(action_str)

            for finding in Finding.objects.all():
                if condition(finding):  # type: ignore (dynamic variable)
                    action(finding)  # type: ignore (dynamic valiable)
        except Exception as msg:
            logger.exception("Error executing filter %s: %s", self.title, msg)
