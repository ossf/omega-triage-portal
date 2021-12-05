import json
import logging
import os
from base64 import b64encode

from django.contrib.auth.decorators import login_required
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from packageurl import PackageURL

from triage.models import Finding, Scan
from triage.util.azure_blob_storage import ToolshedBlobStorageAccessor
from triage.util.finding_importers.sarif_importer import SARIFImporter
from triage.util.search_parser import parse_query_to_Q
from triage.util.source_viewer import path_to_graph
from triage.util.source_viewer.viewer import SourceViewer

logger = logging.getLogger(__name__)


def show_findings(request: HttpRequest) -> HttpResponse:
    """Shows findings based on a query.

    Params:
        q: query to search for, or all findings if not provided
    """
    query = request.GET.get("q", "").strip()
    findings = Finding.objects.all()  # Default
    if query:
        query_object = parse_query_to_Q(query)
        if query_object:
            findings = findings.filter(query_object)
    context = {"query": query, "findings": findings}

    return render(request, "triage/findings_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def show_upload(request: HttpRequest) -> HttpResponse:
    """Show the upload form for findings (SARIF, etc.)"""
    if request.method == "GET":
        return render(request, "triage/findings_upload.html")

    if request.method == "POST":
        package_url = request.POST.get("package_url")
        files = request.FILES.getlist("sarif_file[]")

        if not files:
            return HttpResponseBadRequest("No files provided")

        for file in files:
            try:
                importer = SARIFImporter.import_sarif_file(
                    package_url, json.load(file), request.user
                )
            except:  # pylint: disable=bare-except
                logger.warning("Failed to import SARIF file", exc_info=True)

        return redirect("/findings/upload?status=success")


def show_finding_by_uuid(request: HttpRequest, finding_uuid) -> HttpResponse:
    finding = get_object_or_404(Finding, uuid=finding_uuid)
    from django.contrib.auth.models import User

    assignee_list = User.objects.all()
    context = {"finding": finding, "assignee_list": assignee_list}
    return render(request, "triage/findings_show.html", context)


@require_http_methods(["POST"])
def api_update_finding(request: HttpRequest) -> JsonResponse:
    """Updates a Finding."""

    finding_uuid = request.POST.get("finding_uuid")
    finding = get_object_or_404(Finding, uuid=finding_uuid)
    # if not finding.can_edit(request.user):
    #    return HttpResponseForbidden()

    # Modify only these fields, if provided
    fields = ["analyst_impact", "confidence", "analyst_severity_level"]
    is_modified = False
    for field in fields:
        if field in request.POST:
            value = request.POST.get(field)
            if getattr(finding, field) != value:
                setattr(finding, field, value)
                is_modified = True

    if is_modified:
        finding.save()
        return JsonResponse({"status": "ok"})
    else:
        return JsonResponse({"status": "ok, not modified"})


def api_get_source_code(request: HttpRequest) -> JsonResponse:
    """Returns the source code for a finding."""
    scan_uuid = request.GET.get("scan_uuid")
    file_path = request.GET.get("file_path")
    if scan_uuid:
        scan = get_object_or_404(Scan, uuid=scan_uuid)
        if file_path.startswith("package/"):
            source_code = scan.get_package_contents(file_path)
        elif file_path.startswith("tools/"):
            source_code = scan.get_file_contents(file_path)
        else:
            logger.warning("Invalid prefix for file_path: %s", file_path)
            source_code = None

        if source_code is not None:
            if source_code == b"":
                source_code = b"<Empty File>"
            return JsonResponse(
                {
                    "file_contents": b64encode(source_code).decode("utf-8"),
                    "file_name": os.path.basename(file_path),
                    "status": "ok",
                }
            )
        logger.info("Source code not found for %s", file_path)
        return JsonResponse({"status": "error", "message": "File not found"}, status=404)

    return JsonResponse({"status": "error"}, status=500)


@cache_page(60 * 5)
def api_get_files(request: HttpRequest) -> JsonResponse:
    """Returns a list of files related to a finding."""
    finding_uuid = request.GET.get("finding_uuid")
    finding = get_object_or_404(Finding, uuid=finding_uuid)

    accessor = ToolshedBlobStorageAccessor(finding.scan)
    file_listing = accessor.get_all_files()

    source_graph = path_to_graph(
        file_listing,
        finding.scan.project_version.package_url,
        separator="/",
        root="Root",
    )

    return JsonResponse({"data": source_graph, "status": "ok"})


def api_get_file_list(request: HttpRequest) -> JsonResponse:
    """Returns a list of files in a project."""
    finding_uuid = request.GET.get("finding_uuid")
    finding = get_object_or_404(Finding, uuid=finding_uuid)
    source_code = finding.scan.get_file_list()
    source_graph = path_to_graph(source_code, finding.scan.project_version.package_url)

    return JsonResponse({"data": source_graph, "status": "ok"})


def api_get_blob_list(request: HttpRequest) -> JsonResponse:
    """Returns a list of files in a project."""
    finding_uuid = request.GET.get("finding_uuid")
    finding = get_object_or_404(Finding, uuid=finding_uuid)
    source_code = finding.scan.get_blob_list()
    source_graph = path_to_graph(
        map(lambda s: s.get("relative_path"), source_code), finding.scan.project_version.package_url
    )

    return JsonResponse({"data": source_graph, "status": "ok"})


@csrf_exempt
@require_http_methods(["POST"])
def api_add(request: HttpRequest) -> JsonResponse:
    """Inserts data into the database.

    Required:
    - sarif => the SARIF content (file contents)
    - package_url => the package URL (must include version)
    - scan_artifact => an archive of the content analyzed
    """
    sarif = request.FILES.get("sarif")
    if sarif is None:
        return JsonResponse({"error": "No sarif provided"})
    sarif_content = json.load(sarif)

    scan_artifact = request.FILES.get("scan_artifact")
    if scan_artifact is None:
        return JsonResponse({"error": "No scan_artifact provided"})

    try:
        package_url = PackageURL.from_string(request.POST.get("package_url"))
        if package_url.version is None:
            raise ValueError("Missing version")
    except ValueError:
        return JsonResponse({"error": "Invalid or missing package url"})

    SARIFImporter.import_sarif_file(package_url, sarif_content, scan_artifact.read())
    return JsonResponse({"success": True})
