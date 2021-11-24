from packageurl import PackageURL

def get_complex(obj, key, default_value=""):
    """Get a value from the dictionary d by nested.key.value.
    If keys contain periods, then use key=['a','b','c'] instead."""
    if not obj or not isinstance(obj, dict):
        return default_value
    _data = obj
    try:
        parts = key.split(".") if isinstance(key, str) else key

        for inner_key in parts:
            _data = _data[inner_key]
        return _data
    except Exception:
        return default_value

def modify_purl(purl: PackageURL, **kwargs) -> PackageURL:
    """Modify a PackageURL by adding or replacing values in kwargs."""
    return PackageURL(**(purl.to_dict() | kwargs))