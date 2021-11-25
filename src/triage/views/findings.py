import json
import logging
import os
from base64 import b64encode

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from packageurl import PackageURL

from triage.models.models import Finding
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
    query = request.GET.get("q")
    findings = Finding.objects.all()  # Default
    if query:
        query_object = parse_query_to_Q(query)
        if query_object:
            findings = findings.filter(query_object)
    context = {"query": query, "findings": findings}

    return render(request, "triage/findings_show.html", context)


@require_http_methods(["GET", "POST"])
def show_upload(request: HttpRequest) -> HttpResponse:
    """Show the upload form for findings (SARIF, etc.)"""
    if request.method == "GET":
        return render(request, "triage/findings_upload.html")

    if request.method == "POST":
        package_url = request.POST.get("package_url")
        files = request.FILES.getlist("sarif_file")

        if not files:
            return HttpResponseBadRequest("No files provided")

        for file in files:
            try:
                importer = SARIFImporter.import_sarif_file(package_url, json.load(file))
            except:  # pylint: disable=bare-except
                logger.warning("Failed to import SARIF file", exc_info=True)

        return render(request, "triage/findings_upload.html", {"status": "ok"})


def show_finding_by_uuid(request: HttpRequest, finding_uuid) -> HttpResponse:
    finding = get_object_or_404(Finding, uuid=finding_uuid)
    return render(request, "triage/findings_show.html", {"finding": finding})


@require_http_methods(["POST"])
def api_update_finding(request: HttpRequest) -> JsonResponse:
    """Updates a Finding."""

    finding_uuid = request.POST.get("uuid")
    finding = get_object_or_404(Finding, uuid=finding_uuid)
    if not finding.can_edit(request.user):
        return HttpResponseForbidden()

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
    finding_uuid = request.GET.get("finding-uuid")
    if finding_uuid:
        finding = get_object_or_404(Finding, uuid=finding_uuid)
        # if not finding.can_view(request.user):
        #    return HttpResponseForbidden()

        return JsonResponse(
            {
                "file_contents": b64encode(finding.get_source_code()).decode("utf-8"),
                "file_name": os.path.basename(finding.file_path),
                "file_location": finding.file_line,
                "status": "ok",
            }
        )
    package_url = request.GET.get("package_url")
    file_path = request.GET.get("file_path")
    if package_url and file_path:
        viewer = SourceViewer(package_url)
        res = viewer.get_file(file_path)
        if res:
            return JsonResponse(
                {
                    "file_contents": b64encode(res.get("content")).decode("utf-8"),
                    "file_name": file_path,
                    "status": "ok",
                }
            )

    return JsonResponse({"status": "error"})


def api_get_files(request: HttpRequest) -> JsonResponse:
    """Returns a list of files related to a finding."""
    finding_uuid = request.GET.get("finding_uuid")
    finding = get_object_or_404(Finding, uuid=finding_uuid)

    accessor = ToolshedBlobStorageAccessor(finding.scan)
    tool_files = accessor.get_tool_files()
    package_files = accessor.get_package_files()
    intermediate_files = accessor.get_intermediate_files()

    source_graph = path_to_graph(
        package_files + tool_files + intermediate_files, finding.scan.project_version.package_url
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
