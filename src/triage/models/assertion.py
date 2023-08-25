import os
from django.db import models


class AssertionsPerPackage(models.Model):
    """All assertions of a Package"""

    total_assertions = models.PositiveIntegerField()
    package_name = models.CharField(max_length=100)
    package_uuid = models.UUIDField(unique=True)
    url = models.URLField(max_length=150, default=None)

    def __str__(self):
        return f"Assertion Summary for {self.package_name}"

    def save(self, *args, **kwargs):
        if self.package_uuid and not self.url:
            # Generate the URL based on package_uuid and fixed URL pattern
            assertion_url = os.environ.get(
                "ASSERTION_URL",
            )  # Gets the environment variable for the assertion URL
            self.url = f"{assertion_url}{self.package_uuid}"
        super().save(*args, **kwargs)


class Assertion(models.Model):
    """An assertion of a package"""

    assertion_uuid = models.UUIDField(unique=True)
    assertion_name = models.CharField(max_length=100, default=None)
    assertions_per_package = models.ForeignKey(
        to="AssertionsPerPackage",
        on_delete=models.CASCADE,
        default=None,
    )

    def __str__(self):
        return f"Assertion: {self.assertion_name}"
