import orca

def meta(**kwargs):
    """
    Decorates functions that will be injected into other functions.
    """
    def decorator(func):
        name = func.__name__
        if not hasattr(orca, 'meta'):
            orca.meta = {}
        if name not in orca.meta:
            orca.meta[name] = {}
        for k, v in kwargs.items():
            orca.meta[name][k] = v
    return decorator
