import logging

import markdown
from django import template
from markdown.extensions.wikilinks import WikiLinkExtension

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def wiki_markdown(context):
    if not context:
        return ""
    try:
        extensions = [WikiLinkExtension(base_url="/wiki/", end_url="")]
        result = markdown.markdown(context, extensions=extensions)
        return result
    except Exception as msg:  # pylint: disable=broad-except
        logger.warning("Error in wiki_markdown: %s", msg)
        return context
