import orca


def group(groupname='Group1', order=1):
    """
    Decorates functions that will be injected into other functions.
    """
    def decorator(func):
        name = func.__name__
        orcafunc_wrapper = orca._STEPS.get(
            name, orca._injectable_function.get(
                name, orca._INJECTABLES.get(name)))
        if orcafunc_wrapper:
            if not hasattr(orca, 'meta'):
                orca.meta = {}
            if name not in orca.meta:
                orca.meta[name] = {}
            orca.meta[name]['group'] = groupname
            orca.meta[name]['order'] = order
        return func
    return decorator
