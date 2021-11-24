from django.shortcuts import render
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)

def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'triage/home.html', {})