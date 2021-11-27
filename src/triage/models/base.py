from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseTimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseUserTrackedModel(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")

    class Meta:
        abstract = True


class WorkItemState(models.TextChoices):
    NEW = "N", _("New")
    ACTIVE = "A", _("Active")
    RESOLVED = "R", _("Resolved")
    DELETED = "D", _("Deleted")
    CLOSED = "CL", _("Closed")
    NOT_SPECIFIED = "NS", _("Not Specified")
