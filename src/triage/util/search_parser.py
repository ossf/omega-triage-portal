import logging

import pyparsing as pp
from django.db.models import Q

from triage.models import Finding

logger = logging.getLogger(__name__)


def parse_query_to_Q(query):
    """
    Parse a query string into a list of tokens.
    """

    # Define the grammar
    assigned_to_clause = pp.Group(
        pp.Keyword("assigned_to").suppress()
        + pp.Suppress(":")
        + pp.Word(pp.alphanums).setResultsName("username")
    ).setResultsName("assigned_to")
    severity_clause = pp.Group(
        pp.Keyword("severity").suppress()
        + pp.Suppress(":")
        + pp.delimited_list(pp.one_of(["critical", "important", "moderate", "low"]))
    ).setResultsName("severity")
    updated_dt_clause = pp.Group(
        pp.Keyword("updated:").suppress()
        + pp.one_of(["<", ">", "<=", ">=", "=="]).setResultsName("op")
        + pp.pyparsing_common.iso8601_date("datetime")
    ).setResultsName("updated_dt")
    purl_clause = pp.Group(
        pp.Keyword("purl").suppress()
        + pp.Suppress(":")
        + pp.Word(pp.alphanums + ":@/?=-.").setResultsName("purl")
    ).setResultsName("purl")
    other_clause = pp.Word(pp.alphas).setResultsName("text_search")
    clause = assigned_to_clause | severity_clause | updated_dt_clause | purl_clause | other_clause
    full_clause = pp.OneOrMore(clause)

    # Parse the query
    try:
        results = full_clause.parse_string(query)
    except:
        logger.error("Failed to parse query: %s", query)
        return None

    # Assemble the Q object
    q = Q()
    if results.assigned_to:
        q = q & Q(assigned_to__username=results.assigned_to.username)

    if results.severity:
        severities = map(Finding.SeverityLevel.parse, results.severity.asList())
        q = q & Q(severity_level__in=list(severities))

    if results.updated_dt:
        if results.updated_dt.op == "<":
            q = q & Q(updated_at__lt=results.updated_dt.datetime)
        elif results.updated_dt.op == ">":
            q = q & Q(updated_at__gt=results.updated_dt.datetime)
        elif results.updated_dt.op == "<=":
            q = q & Q(updated_at__lte=results.updated_dt.datetime)
        elif results.updated_dt.op == ">=":
            q = q & Q(updated_at__gte=results.updated_dt.datetime)
        elif results.updated_dt.op == "==":
            q = q & Q(updated_at__exact=results.updated_dt.datetime)

    if results.purl:
        q = q & Q(scan__project_version__project__package_url=results.purl.purl)

    if results.text_search:
        q = q & Q(title__icontains=results.text_search)
    return q
