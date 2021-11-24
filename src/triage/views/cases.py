import os
from triage.util.source_viewer.viewer import SourceViewer
from triage.util.source_viewer import path_to_graph
from base64 import b64encode
from triage.util.finding_importers.sarif_importer import SARIFImporter
from triage.util.azure_blob_storage import ToolshedBlobStorageAccessor
import json
import uuid
from django.shortcuts import render, get_object_or_404
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
    HttpResponseForbidden
)
from packageurl import PackageURL
from django.views.decorators.csrf import csrf_exempt
from typing import Any, List
from triage.models.models import Case, ProjectVersion, Project
from django.views.decorators.http import require_http_methods
from triage.util.search_parser import parse_query_to_Q

def show_cases(request: HttpRequest) -> HttpResponse:
    """Shows cases based on a query.
    
    Params:
        q: query to search for, or all findings if not provided
    """
    query = request.GET.get('q', '')
    c = {
        'query': query, 
        'cases': Case.objects.all(),
        'case_states': Case.State.choices,
        'reporting_partner': Case.CasePartner.choices
    }
    return render(request, 'triage/case_show.html', c)
