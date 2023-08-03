import logging
import pathlib
import hashlib
import graphene
from graphene_file_upload.scalars import Upload

import graphql_jwt
from graphql_jwt.decorators import login_required

from django.core.exceptions import ValidationError
from packageurl import PackageURL
from triage.models import ProjectVersion
from triage.util.finding_importers.archive_importer import ArchiveImporter

logger = logging.getLogger(__name__)
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024  # Allowed file size: 200 MB in bytes
ALLOWED_EXTENSIONS = [".sarif"]  # Allowed extension: SARIF file


class Query(graphene.ObjectType):
    """Root Query for the application."""

    dummy = graphene.String(description="A dummy query for testing purposes.")

    def resolve_dummy(self, info):
        """This method returns a dummy string for testing purposes."""
        return "Dummy query"


class UploadFileMutation(graphene.Mutation):
    """Mutation to upload a file to the Triage Portal"""

    class Arguments:
        file = Upload(required=True, description="The file to upload.")
        package_url = graphene.String(required=True, description="The package URL.")
        checksum = graphene.String(
            required=True,
            description="The checksum of the file.",
        )

    success = graphene.Boolean(
        description="Indicates if the file upload was successful.",
    )
    errors = graphene.List(
        graphene.String,
        description="List of errors that occurred during file upload.",
    )
    success_message = graphene.String(
        description="Success message if file upload is successful.",
    )

    @classmethod
    @login_required
    def mutate(cls, root, info, file, package_url, checksum):
        """Mutate method for the upload file mutation.

        This method handles the mutation logic for uploading a file to the Triage Portal,
        associating it with a project version specified by the package URL, and verifying
        the checksum of the uploaded file. The file processing logic is also performed in
        this method to import the contents of the uploaded file to the portal.

        Args:
            root: The root of the mutation (not used in this case).
            info: The GraphQL Resolve Info.
            file: The uploaded file.
            package_url (str): The package URL specifying the project version.
            checksum (str): The checksum of the file.

        Returns:
            UploadFileMutation: An instance of the UploadFileMutation.
        """
        # Access the authenticated user
        user = info.context.user

        # Verify user authentication and if it is not anonymous
        if not user.is_authenticated or user.is_anonymous:
            raise Exception("User authentication failed")

        validate_file_extension(file)  # Validate file extension
        validate_file_size(file)  # Validate file size
        validate_checksum(file, checksum)  # Validate checksum

        # Perform the file processing logic
        errors = process_file(file, package_url, user)

        # Success is set based on whether there are any errors
        if errors:
            return UploadFileMutation(success=False, errors=errors)

        # Array is empty, so file upload is successful
        return UploadFileMutation(success=True, errors=errors)


def validate_file_extension(file):
    """Validates that only SARIF files can be uploaded to the API endpoint.

    This function checks the file extension of the uploaded file and
    verifies whether it is a supported SARIF file.

    Args:
        file: The uploaded file.

    Raises:
        ValidationError: If the file has an unsupported format.

    Returns:
        bool: True if the file extension is supported (SARIF file).
    """
    file_extension = pathlib.Path(file.name).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        logger.error(
            "The file extension %s is an unsupported format. Only %s files are allowed.",
            file_extension,
            ALLOWED_EXTENSIONS,
        )
        raise ValidationError("Unsupported file format. Only SARIF files are allowed.")
    return True


def validate_file_size(file):
    """Validates that the uploaded file does not exceed the maximum allowed size.

    Args:
        file: The uploaded file.

    Raises:
        ValidationError: If the file size exceeds the maximum allowed limit.

    Returns:
        bool: True if the file size is within the allowed limit.
    """
    if file.size > MAX_FILE_SIZE_BYTES:
        logger.error(
            "File size: %s, Maximum allowed file size: %s",
            file.size,
            MAX_FILE_SIZE_BYTES,
        )
        raise ValidationError("File size exceeds the maximum allowed limit.")
    return True


def validate_checksum(file, checksum):
    """Generate checksum for the file based on the MD5 hash function.

    This function calculates the MD5 hash value of the file's contents
    and compares it with the provided checksum to ensure the file
    has not been corrupted during transfer.

    Args:
        file: The uploaded file.
        checksum (str): The provided checksum to compare.

    Raises:
        ValidationError: If the checksum validation fails.

    Returns:
        bool: True if the checksum validation is successful.
    """
    file_data = file.read()  # Read the file contents
    calculated_checksum = hashlib.md5(file_data).hexdigest()  # calculate md5 hash value
    file.seek(0)  # Reset the file pointer to the beginning
    if checksum != calculated_checksum:
        logger.error(
            "Checksum Calculated: %s, Given Checksum: %s",
            calculated_checksum,
            checksum,
        )
        raise ValidationError("Checksum Validation Failed")
    return True


def process_file(file, package_url, user):
    """Function that retrieves the project version and imports the file to the portal.

    This function takes an uploaded file, a package URL, and a user object to associate
    the uploaded file with a project version. The function retrieves or creates the
    appropriate project version based on the package URL, downloads the source code
    associated with the project version, and imports the contents of the uploaded file
    to the portal.

    Args:
        file: The uploaded file.
        package_url (str): The package URL.
        user: The authenticated user associated with the file upload.

    Returns:
        list: A list of error messages encountered during the file processing.
    """
    url = PackageURL.from_string(package_url)

    errors = []

    # Retrieve the project version
    project_version = ProjectVersion.get_or_create_from_package_url(
        url,
        user,
    )

    # Find the source code for this project version
    # Get the source based on the package url
    project_version.download_source_code()

    try:
        archive_importer = ArchiveImporter()
        try:
            archive_importer.import_archive(
                file.name,
                file.read(),
                project_version,
                user,
            )
        except Exception as msg:
            errors.append(f"Failed to import archive: {file.name}")
    except:
        logger.warning("Failed to import SARIF file", exc_info=True)

    return errors


class Mutation(graphene.ObjectType):
    """Root Mutation for the application."""

    upload_file = UploadFileMutation.Field(
        description="Upload a file, project version, and checksum of it.",
    )
    # jwt mutations
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field(
        description="Validates the token and obtain the token payload",
    )


schema = graphene.Schema(query=Query, mutation=Mutation)
