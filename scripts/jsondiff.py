import operator

def get_differences(a, b, exclusions=None, parent_path=None):
    """Return the list of differences between two lists or two dicts."""
    
    exclusions = exclusions or []
    parent_path = parent_path or []
    
    fields = []
    fields.extend(_get_fields(a))
    fields.extend(x for x in _get_fields(b) if x not in fields)
    
    differences = []
    for field in fields:
        if field in exclusions:
            continue
        
        path = parent_path+[field]
        
        in_a, item_a = _get_field(a, field)
        in_b, item_b = _get_field(b, field)
        
        if not in_a:
            # Added in b
            differences.append((path, "added", b[field]))
        elif not in_b:
            # Deleted in b
            differences.append((path, "deleted", a[field]))
        else:
            # Modified
            if type(item_a) != type(item_b):
                differences.append((path, "type modified", type(item_a), type(item_b)))
            else:
                if isinstance(item_a, list) or isinstance(item_a, dict):
                    differences.extend(
                        get_differences(item_a, item_b, exclusions, path))
                else:
                    # Scalar values
                    is_equal = None
                    if isinstance(item_a, float):
                        is_equal = lambda x,y: (
                            ((-1e-5) < (x-y)/x < (+1e-5)) if x != 0
                            else abs(x-y) < 1e-6)
                    else:
                        is_equal = operator.eq
                    if not is_equal(item_a, item_b):
                        differences.append((path, "value modified", a[field], b[field]))
    
    return differences

def _get_fields(value):
    """Return the fields of a list or a dict."""
    if isinstance(value, list):
        return range(len(value))
    elif isinstance(value, dict):
        return value.keys()
    else:
        raise Exception("Not a list or a dict")

def _get_field(struct, field):
    """Return whether the field is in the structure, and the eventual value."""
    
    try:
        item = struct[field]
        in_struct = True
    except:
        in_struct = False
        item = None
    
    return (in_struct, item)
