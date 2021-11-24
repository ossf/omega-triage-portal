from django.shortcuts import render, redirect
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.views.decorators.http import require_http_methods
from triage.models.models import Filter

@require_http_methods(["GET"])
def index(request: HttpRequest) -> HttpResponse:
    """Show a list of filters."""
    project_id = request.GET.get('project_id')
    if project_id:
        filters = Filter.objects.filter(project__id=project_id)
    else:
        filters = Filter.objects.filter(project__isnull=True)

    return render(request, 'triage/filters/index.html')

@require_http_methods(["GET"])
def new_filter(request: HttpRequest) -> HttpResponse:
    """Show a form to create a new filter."""
    return render(request, 'triage/filters/new.html')

@require_http_methods(["GET"])
def show_filter(request: HttpRequest) -> HttpResponse:
    """Show a filter."""
    filter_id = request.GET.get('filter_id')
    if filter_id:
        filter = Filter.objects.get(id=filter_id)
        return render(request, 'triage/filters/show.html', {'filter': filter})
    else:
        return HttpResponseNotFound()

@require_http_methods(["POST"])
def edit_filter(request: HttpRequest) -> HttpResponse:
    """Edit a filter."""
    filter_id = request.POST.get('filter_id')
    if not filter_id:
        return HttpResponseBadRequest()
    
    name = request.POST.get('name')
    definition = request.POST.get('definition')
    active = request.POST.get('active')
    priority = request.POST.get('priority')
    
    if not name or not definition or not active or not priority:
        return HttpResponseBadRequest()
    
    filter = Filter.objects.get(id=filter_id)
    filter.name = name
    filter.definition = definition
    filter.active = active
    filter.priority = priority
    filter.save()

    return redirect(filter)


