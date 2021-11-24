import logging

logger = logging.getLogger(__name__)

"""
Example:
input:
["/foo", "/foo/bar", "/foo/bar/baz"]
output:
[{
    id: "/foo"
    full_path: "/foo"
]

"""
def path_to_graph(paths, package_url, separator="/", root=None):
    """
    Converts a list of paths into a graph suitable for jstree.

    Args:
        paths: list of paths
        separator: path separator
        root: root directory to pin the graph to

    Returns:
     a list of dictionaries containing the relevant
     fields for jstree.
    """
    if not paths:
        return []

    result = []
    seen_nids = set()
    
    if root:
        result.append(
            {
                "id": root,  # TODO minimize this via a lookup table
                "full_path": "#",
                "text": root,
                "parent": "#",
                "package_url": None,
                "path": "/",
                "file_id": None,
                "icon": "",
            }
        )
    else:
        root = "#"

    for path in paths:
        if not isinstance(path, str) or not path or path.startswith("pkg:"):
            logger.debug('Ignoring invalid path [%s]', path)
            continue

        if not path.startswith(separator):
            path = separator + path

        path_parts = path.split(separator)[1:]
        
        logging.debug(f"Analyzing: %s", path_parts)
        for (part_id, part) in enumerate(path_parts):
            if part_id == 0:
                parent_id = root
                node_id = part
            else:
                parent_id = separator.join(path_parts[:part_id])
                node_id = separator.join(path_parts[:(part_id + 1)])
            node_name = part

            if node_name and node_id not in seen_nids:
                result.append(
                    {
                        "id": node_id,  # TODO minimize this via a lookup table
                        "full_path": node_id,
                        "text": node_name,
                        "parent": parent_id,
                        "package_url": package_url,
                        "li_attr": {
                            "package_url": package_url
                        },
                        "path": node_id,
                        "icon": "fas fa-code" if part_id == len(path_parts) else "",
                    }
                )
                seen_nids.add(node_id)
    return result
