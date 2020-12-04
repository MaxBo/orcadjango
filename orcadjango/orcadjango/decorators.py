import orca


def meta(**kwargs):
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
            for k, v in kwargs.items():
                orca.meta[name][k] = v
        return func
    return decorator
