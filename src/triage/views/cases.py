import json
import os
import uuid
from base64 import b64encode
from typing import Any, List

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from packageurl import PackageURL

from triage.models import Case, Project, ProjectVersion, WorkItemState
from triage.util.azure_blob_storage import ToolshedBlobStorageAccessor
from triage.util.finding_importers.sarif_importer import SARIFImporter
from triage.util.search_parser import parse_query_to_Q
from triage.util.source_viewer import path_to_graph
from triage.util.source_viewer.viewer import SourceViewer


def show_cases(request: HttpRequest) -> HttpResponse:
    """Shows cases based on a query.

    Params:
        q: query to search for, or all findings if not provided
    """
    query = request.GET.get("q", "")
    c = {
        "query": query,
        "cases": Case.objects.all(),
        "case_states": WorkItemState.choices,
        "reporting_partner": Case.CasePartner.choices,
    }
    return render(request, "triage/case_show.html", c)


@require_http_methods(["GET"])
def new_case(request: HttpRequest) -> HttpResponse:
    """Shows the new case form."""
    if request.method == "GET":
        context = {
            "case_states": WorkItemState.choices,
            "reporting_partner": Case.CasePartner.choices,
        }
        return render(request, "triage/case_new.html", context)
    return HttpResponseBadRequest()
