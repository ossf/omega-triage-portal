from django import template
from packageurl import PackageURL

register = template.Library()


class ParsePackageURL(template.Node):
    def __init__(self, project):
        self.project = project
        print(project)

    def render(self, context):
        try:
            package_url = self.project.package_url
            context.update({"package_url": package_url.to_dict()})
        except Exception as msg:
            print(msg)
        return ""


@register.tag(name="parse_package_url")
def do_parse_package_url(parser, token):
    print(token.contents.split()[1])
    return ParsePackageURL(token)
