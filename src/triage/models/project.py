import logging
import os
import subprocess
import tempfile
import uuid

import magic
from django.contrib.auth.models import User
from django.db import models
from packageurl import PackageURL

from core.settings import OSSGADGET_PATH
from triage.models.base import BaseTimestampedModel, BaseUserTrackedModel
from triage.models.file import File
from triage.util.content_managers.file_manager import FileManager
from triage.util.general import modify_purl

logger = logging.getLogger(__name__)


class Project(BaseTimestampedModel, BaseUserTrackedModel):
    """An abstract project undergoing analysis."""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        unique=True,
    )
    name = models.CharField(max_length=1024, db_index=True)
    package_url = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        db_index=True,
    )
    metadata = models.JSONField(null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/projects/{self.uuid}"


class ProjectVersion(BaseTimestampedModel, BaseUserTrackedModel):
    """A version of a project."""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        unique=True,
    )
    project = models.ForeignKey("Project", on_delete=models.CASCADE)
    package_url = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        db_index=True,
    )
    files = models.ManyToManyField("File", blank=True, editable=True)
    metadata = models.JSONField(null=True)

    def __str__(self):
        return self.package_url

    def get_absolute_url(self):
        return f"/projects/{self.project.uuid}/{self.uuid}"

    @classmethod
    def get_or_create_from_package_url(
        cls,
        package_url: PackageURL,
        created_by: User,
    ) -> "ProjectVersion":
        """Retrieves or create a PackageVersion from the given package_url."""
        if package_url is None:
            raise ValueError("'package_url' cannot be None.")

        package_url_no_version = modify_purl(package_url, version=None)

        if package_url.namespace:
            package_name = f"{package_url.namespace}/{package_url.name}"
        else:
            package_name = package_url.name

        project, _ = Project.objects.get_or_create(
            package_url=str(package_url_no_version),
            defaults={
                "name": package_name,
                "created_by": created_by,
                "updated_by": created_by,
            },
        )
        project_version, _ = cls.objects.get_or_create(
            project=project,
            package_url=str(package_url),
            defaults={"created_by": created_by, "updated_by": created_by},
        )
        return project_version

    def download_source_code(self):
        """Retrieves the source code for this ProjectVersion and connects it to this object."""
        if self.package_url is None:
            raise ValueError("The package_url must not be None.")

        file_manager = FileManager()
        with tempfile.TemporaryDirectory() as temp_directory:
            # pylint: disable=subprocess-run-check
            res = subprocess.run(
                ["./oss-download", "-e", "-x", temp_directory, self.package_url],
                capture_output=True,
                cwd=OSSGADGET_PATH,
            )
            if res.returncode != 0 or not os.listdir(temp_directory):
                logger.debug("Failed to load source for package %s", self.package_url)
                raise OSError("Failed to download package")

            num_added = 0
            for root, _, files in os.walk(temp_directory):
                for file in files:
                    full_path = os.path.join(root, file)
                    relative_path = full_path[len(temp_directory) + 1 :].replace(
                        "\\",
                        "/",
                    )

                    with open(full_path, "rb") as f:
                        content = f.read()
                    mime_type = magic.from_buffer(content, mime=True)

                    logger.debug("Adding [%s]", relative_path)
                    file_key = file_manager.add_file(
                        content,
                        relative_path,
                        exist_ok=True,
                    )

                    # Files are unique by content, path, etc.
                    file = File.objects.get_or_create(
                        name=os.path.basename(relative_path),
                        path=relative_path,
                        content_type=mime_type,
                        file_key=file_key,
                        file_type=File.FileType.SOURCE_CODE,
                    )[0]
                    self.files.add(file)
                    num_added += 1

            self.save()
            logger.debug("Added %d files.", num_added)
