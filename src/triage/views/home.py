from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render

from triage.models import Case, Finding


def home(request: HttpRequest) -> HttpResponse:
    finding_last_updated = Finding.objects.all().order_by("-updated_at").first().created_at
    case_last_updated = Case.objects.all().order_by("-updated_at").first().created_at
    context = {"finding_last_updated": finding_last_updated, "case_last_updated": case_last_updated}
    return render(request, "triage/home.html", context)
