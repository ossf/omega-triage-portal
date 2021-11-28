import logging
import uuid
from typing import Optional

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from packageurl import PackageURL

from triage.models.base import BaseTimestampedModel, BaseUserTrackedModel, WorkItemState
from triage.util.azure_blob_storage import (
    AzureBlobStorageAccessor,
    ToolshedBlobStorageAccessor,
)
from triage.util.general import modify_purl
from triage.util.source_viewer.viewer import SourceViewer

logger = logging.getLogger(__name__)


class Tool(BaseTimestampedModel, BaseUserTrackedModel):
    """A tool used to create a finding."""

    class ToolType(models.TextChoices):
        NOT_SPECIFIED = "NS", _("Not Specified")
        MANUAL = "MA", _("Manual")
        STATIC_ANALYSIS = "SA", _("Static Analysis")
        OTHER = "OT", _("Other")

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=128)
    friendly_name = models.CharField(max_length=128, blank=True, null=True)
    version = models.CharField(max_length=64, blank=True)
    type = models.CharField(max_length=2, choices=ToolType.choices, default=ToolType.NOT_SPECIFIED)
    active = models.BooleanField(default=True)

    def __str__(self):
        parts = []
        if self.friendly_name:
            parts.append(self.friendly_name)
        else:
            parts.append(self.name)
        if self.version:
            parts.append(self.version)
        return " ".join(parts)

    def save(self, *args, **kwargs):
        if self.friendly_name is None:
            self.friendly_name = self.name
        super().save(*args, **kwargs)


class Project(BaseTimestampedModel, BaseUserTrackedModel):
    """An abstract project undergoing analysis."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=1024, db_index=True)
    package_url = models.CharField(max_length=1024, null=True, blank=True, db_index=True)
    metadata = models.JSONField(null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/projects/{self.uuid}"


class ProjectVersion(BaseTimestampedModel, BaseUserTrackedModel):
    """A version of a project."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    package_url = models.CharField(max_length=1024, null=True, blank=True, db_index=True)
    metadata = models.JSONField(null=True)

    def __str__(self):
        return self.package_url

    def get_absolute_url(self):
        return f"/projects/{self.project.uuid}/{self.uuid}"

    @classmethod
    def get_or_create_from_package_url(
        cls, package_url: PackageURL, created_by: User
    ) -> "ProjectVersion":
        """Retrieves or create a PackageVersion from the given package_url."""
        if package_url is None:
            raise ValueError("'package_url' cannot be None.")

        package_url_no_version = modify_purl(package_url, version=None)
        project, _ = Project.objects.get_or_create(
            package_url=str(package_url_no_version),
            defaults={"name": package_url.name, "created_by": created_by, "updated_by": created_by},
        )
        project_version, _ = ProjectVersion.objects.get_or_create(
            project=project,
            package_url=package_url,
            defaults={"created_by": created_by, "updated_by": created_by},
        )
        return project_version


class Scan(BaseTimestampedModel, BaseUserTrackedModel):
    """A scan of a project version."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    project_version = models.ForeignKey(ProjectVersion, on_delete=models.CASCADE)
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE)

    artifact_url_base = models.CharField(max_length=1024, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_dt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"An execution of {self.tool} against {self.project_version}"

    def get_absolute_url(self):
        return f"/scan/{self.uuid}"

    def get_file_content(self, filename: str) -> Optional[str]:
        if filename is None:
            return None

        accessor = ToolshedBlobStorageAccessor(self)
        for _filename in accessor.get_all_files():
            print(f"Comparing {_filename} to {filename}")
            if _filename == filename:
                return accessor.get_file_content(_filename)
        return None

    def get_source_files(self) -> list:
        """Retreives the source code for this scan."""
        accessor = ToolshedBlobStorageAccessor(self)
        return accessor.get_source_files()

    def get_source_code(self, filename: str) -> Optional[str]:
        """Retreives the source code for a file."""

        viewer = SourceViewer(self.project_version.package_url)
        res = viewer.get_file(filename)
        if res:
            return res.get("content")
        return None

    def get_file_list(self) -> list:
        """Retreives a list of files in the scan."""
        viewer = SourceViewer(self.project_version.package_url)
        return viewer.get_file_list()

    def get_blob_list(self) -> list:
        """Retreives a list of blobs in the scan."""
        purl = PackageURL.from_string(self.project_version.package_url)
        if purl.namespace:
            prefix = f"{purl.type}/{purl.namespace}/{purl.name}/{purl.version}"
        else:
            prefix = f"{purl.type}/{purl.name}/{purl.version}"

        accessor = AzureBlobStorageAccessor(prefix)
        return accessor.get_blob_list()

    def get_file_contents(self, filename) -> Optional[str]:
        """Retreives the contents of a file."""
        accessor = ToolshedBlobStorageAccessor(self)
        return accessor.get_file_contents(filename)


class TriageRule(models.Model):
    """
    ???
    def applies(finding) -> bool
    def action(finding) -> void

    if applies(f): action(f)
    """

    class TriageEvent(models.TextChoices):
        ON_FINDING_NEW = "FN", _("On New Finding")
        ON_FINDING_MODIFIED = "FM", _("On Modified Finding")

    class RuleType(models.TextChoices):
        PYTHON_FUNCTION = "PY", _("Python Function")

    event = models.CharField(
        max_length=2, choices=TriageEvent.choices, default=TriageEvent.ON_FINDING_NEW
    )
    condition = models.TextField(max_length=2048, null=True, blank=True)
    action = models.TextField(max_length=2048, null=True, blank=True)

    active = models.BooleanField(db_index=True, default=True)
    priority = models.PositiveSmallIntegerField(default=1000)

    type = models.CharField(
        max_length=2, choices=RuleType.choices, default=RuleType.PYTHON_FUNCTION
    )


# class File(models.Model):
#    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#    scan = models.ForeignKey(Scan, on_delete=models.CASCADE)#

#    content = models.FileField(upload_to="file_archive")
#    content_hash = models.CharField(max_length=128, db_index=True)
#    path = models.CharField(max_length=4096)


class Finding(BaseTimestampedModel, BaseUserTrackedModel):
    class ConfidenceLevel(models.TextChoices):
        NOT_SPECIFIED = "NS", _("Not Specified")
        VERY_LOW = "VL", _("Very Low")
        LOW = "L", _("Low")
        MEDIUM = "M", _("Medium")
        HIGH = "H", _("High")
        VERY_HIGH = "VH", _("Very High")

    class SeverityLevel(models.TextChoices):
        NOT_SPECIFIED = "NS", _("Not Specified")
        NONE = "NO", _("None")
        INFORMATIONAL = "IN", _("Informational")
        VERY_LOW = "VL", _("Very Low")
        LOW = "L", _("Low")
        MEDIUM = "M", _("Medium")
        HIGH = "H", _("High")
        VERY_HIGH = "VH", _("Very High")

        @classmethod
        def parse(cls, severity: str):
            if severity is None:
                return cls.NOT_SPECIFIED
            severity = severity.lower().strip()
            if severity == "critical":
                return cls.VERY_HIGH
            if severity in ["important", "error"]:
                return cls.HIGH
            if severity in ["moderate", "warn", "warning"]:
                return cls.MEDIUM
            if severity in ["low"]:
                return cls.LOW
            if severity in ["defense-in-depth"]:
                return cls.VERY_LOW
            if severity in ["info", "informational"]:
                return cls.INFORMATIONAL
            if severity in ["fp", "false positive"]:
                return cls.NONE
            return cls.NOT_SPECIFIED

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE)

    title = models.CharField(max_length=1024)

    file_path = models.CharField(max_length=2048)
    file_line = models.PositiveIntegerField(null=True, blank=True)

    # Impact showing how important a finding is to the larger community.
    impact_usage = models.PositiveBigIntegerField(null=True, blank=True)
    impact_context = models.PositiveBigIntegerField(null=True, blank=True)
    analyst_impact = models.PositiveBigIntegerField(null=True, blank=True)

    # Confidence showing how certain a finding is.
    confidence = models.CharField(
        max_length=2, choices=ConfidenceLevel.choices, default=ConfidenceLevel.NOT_SPECIFIED
    )

    # Severity showing how important a finding is to the security quality of a project.
    severity_level = models.CharField(
        max_length=2, choices=SeverityLevel.choices, default=SeverityLevel.NOT_SPECIFIED
    )
    analyst_severity_level = models.CharField(
        max_length=2, choices=SeverityLevel.choices, default=SeverityLevel.NOT_SPECIFIED
    )
    state = models.CharField(max_length=2, choices=WorkItemState.choices, default=WorkItemState.NEW)

    # Who the finding is currently assigned to
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    assigned_dt = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return f"/finding/{self.uuid}"

    @property
    def get_filename_display(self):
        """Render the filename or a placeholder where one does not exist."""
        return self.file_path or "-"

    @property
    def get_severity_display(self):
        """Gets the best severity level (analyst estimate taking precedence)"""
        if self.analyst_severity_level == Finding.SeverityLevel.NOT_SPECIFIED:
            return self.get_severity_level_display()
        return self.get_analyst_severity_level_display()

    @property
    def get_impact_display(self):
        """Gets the best impact level (analyst estimate taking precedence)"""
        if self.analyst_impact is not None:
            return self.analyst_impact
        else:
            return (self.impact_context or 0) * (self.impact_usage or 0)

    def get_source_code(self):
        """Retrieve source code pertaining to this finding."""
        if self.file_path:
            return self.scan.get_source_code(self.file_path)

        logger.debug("No source code available (file_path is empty)")
        return None


class Filter(BaseTimestampedModel, BaseUserTrackedModel):
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    definition = models.TextField()
    active = models.BooleanField(default=True)
    priority = models.PositiveSmallIntegerField(default=1000)

    def is_global(self):
        return self.project is None


class Note(BaseTimestampedModel, BaseUserTrackedModel):
    content = models.TextField()

    def __str__(self):
        return self.content


class Case(BaseTimestampedModel, BaseUserTrackedModel):
    """
    Represents a case that is being reported to a maintainer for a fix.
    """

    class CasePartner(models.TextChoices):
        NONE = "N", _("None")
        GITHUB_SECURITY_LAB = "GS", _("GitHub Security Lab")
        CERT = "CT", _("CERT")
        MSRC = "MS", _("MSRC")
        NOT_SPECIFIED = "NS", _("Not Specified")

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    findings = models.ManyToManyField(Finding, related_name="cases")
    state = models.CharField(max_length=2, choices=WorkItemState.choices, default=WorkItemState.NEW)
    title = models.CharField(max_length=1024)
    description = models.TextField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        User, null=True, blank=True, related_name="assigned_cases", on_delete=models.SET_NULL
    )
    assigned_dt = models.DateTimeField(auto_now_add=True)
    reported_to = models.CharField(max_length=2048, null=True, blank=True)
    reporting_partner = models.CharField(
        max_length=2,
        choices=CasePartner.choices,
        default=CasePartner.NOT_SPECIFIED,
        null=True,
        blank=True,
    )
    report_foreign_reference = models.CharField(max_length=1024, null=True, blank=True)
    resolved_target_dt = models.DateTimeField(null=True, blank=True)
    resolved_dt = models.DateTimeField(null=True, blank=True)
    notes = models.ManyToManyField(Note, related_name="cases")
