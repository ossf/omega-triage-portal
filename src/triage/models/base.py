from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from core import settings


class BaseTimestampedModel(models.Model):
    """A mixin that adds a created/updated date field to a model."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseUserTrackedModel(models.Model):
    """A mixin that adds a created/updated by field to a model."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )

    class Meta:
        abstract = True


class WorkItemState(models.TextChoices):
    """
    This class contains work item state fields, which can be used as choice values
    in other models.
    """

    NEW = "N", _("New")
    ACTIVE = "A", _("Active")
    RESOLVED = "R", _("Resolved")
    DELETED = "D", _("Deleted")
    CLOSED = "CL", _("Closed")
    NOT_SPECIFIED = "NS", _("Not Specified")
