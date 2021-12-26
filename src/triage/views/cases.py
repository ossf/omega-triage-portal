import json
import os
import uuid
from base64 import b64encode
from typing import Any, List
from uuid import UUID

from django.contrib.auth.decorators import login_required
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


@login_required
@require_http_methods(["GET"])
def show_cases(request: HttpRequest) -> HttpResponse:
    """Shows cases based on a query.

    Params:
        q: query to search for, or all findings if not provided
    """
    query = request.GET.get("q", "").strip()
    cases = Case.objects.all()  # Default
    if query:
        query_object = parse_query_to_Q(Case, query)
        if query_object:
            cases = cases.filter(query_object)

    context = {
        "query": query,
        "cases": cases,
        "case_states": WorkItemState.choices,
        "reporting_partner": Case.CasePartner.choices,
    }

    return render(request, "triage/case_list.html", context)


def show_case(request: HttpRequest, case_uuid: UUID) -> HttpResponse:
    """Shows a case."""
    case = get_object_or_404(Case, uuid=str(case_uuid))
    context = {
        "case": case,
        "case_states": WorkItemState.choices,
        "reporting_partner": Case.CasePartner.choices,
    }
    return render(request, "triage/case_show.html", context)


@login_required
@require_http_methods(["GET"])
def new_case(request: HttpRequest) -> HttpResponse:
    """Shows the new case form."""
    context = {
        "case_states": WorkItemState.choices,
        "reporting_partner": Case.CasePartner.choices,
    }
    return render(request, "triage/case_new.html", context)


@login_required
@require_http_methods(["POST"])
def save_case(request: HttpRequest) -> HttpResponse:
    case_uuid = request.POST.get("case_uuid")
    if case_uuid is None:
        case = Case()
    else:
        case = get_object_or_404(Case, uuid=case_uuid)
    case.title = request.POST.get("title")
    case.state = request.POST.get("state")
    case.updated_by = request.user
    case.created_by = request.user

    case.full_clean()
    case.save()

    return HttpResponseRedirect(f"/case/{case_uuid}")
