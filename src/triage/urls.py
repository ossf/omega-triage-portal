# -*- coding: utf-8 -*-
"""This module URL patterns specific to the Triage Portal."""

from django.urls import path

from triage.views import cases, filters, findings, home, tool_defect

urlpatterns = [
    path("cases/", cases.show_cases),
    path("tool_defect/<uuid:tool_defect_uuid>", tool_defect.show_tool_defect),
    path("tool_defect/new", tool_defect.show_add_tool_defect),
    path("tool_defect/save", tool_defect.save_tool_defect),
    path("tool_defect/", tool_defect.show_tool_defects),
    path("api/findings/add", findings.api_add),
    path("api/findings/get_files", findings.api_get_files),
    path("api/findings/get_source_code", findings.api_get_source_code),
    path("api/findings/get_file_list", findings.api_get_file_list),
    path("api/findings/get_blob_list", findings.api_get_blob_list),
    path("findings/<uuid:finding_uuid>", findings.show_finding_by_uuid),
    path("findings/upload", findings.show_upload),
    path("findings/", findings.show_findings),
    path("filters/new", filters.new_filter),
    path("filters", filters.index),
    path("", home.home),
]
