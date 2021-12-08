from uuid import UUID

from django.core.exceptions import ValidationError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from triage.models import Filter
from triage.util.search_parser import parse_query_to_Q


@require_http_methods(["GET"])
def show_filters(request: HttpRequest) -> HttpResponse:
    """Shows filters based on a query.

    Params:
        q: query to search for, or all findings if not provided
    """
    query = request.GET.get("q", "").strip()
    filters = Filter.objects.all()  # Default
    if query:
        query_object = parse_query_to_Q(query)
        if query_object:
            filters = filters.filter(query_object)
    context = {"query": query, "filters": filters}
    return render(request, "triage/filter_list.html", context)


@require_http_methods(["GET"])
def new_filter(request: HttpRequest) -> HttpResponse:
    """Show a form to create a new filter."""
    return render(request, "triage/filter_edit.html")


@require_http_methods(["GET"])
def show_filter(request: HttpRequest, filter_uuid: UUID) -> HttpResponse:
    """Show a filter."""
    if filter_uuid:
        filter = Filter.objects.get(uuid=str(filter_uuid))
        return render(request, "triage/filter_edit.html", {"filter": filter})
    else:
        return HttpResponseNotFound()


def execute_filter(request: HttpRequest) -> JsonResponse:
    """Execute a filter."""
    if request.method == "GET":
        filter_uuid = request.GET.get("filter_uuid")
        if filter_uuid:
            filter = Filter.objects.get(uuid=str(filter_uuid))
            filter.execute()
            return JsonResponse({"status": "success"})
        else:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()


@require_http_methods(["POST"])
def save_filter(request: HttpRequest) -> HttpResponse:
    """Edit a filter."""
    filter_uuid = request.POST.get("filter_uuid")
    if filter_uuid:
        filter = Filter.objects.get(uuid=filter_uuid)
    else:
        filter = Filter()
        filter.created_by = request.user

    filter.title = request.POST.get("title")
    filter.condition = request.POST.get("condition")
    filter.action = request.POST.get("action")
    filter.active = bool(request.POST.get("active"))
    filter.priority = int(request.POST.get("priority"))
    filter.updated_by = request.user

    try:
        filter.full_clean()
    except ValidationError as e:
        return render(
            request, "triage/filter_edit.html", {"filter": filter, "error_messages": e.messages}
        )
    filter.save()

    return HttpResponseRedirect("/filters")
