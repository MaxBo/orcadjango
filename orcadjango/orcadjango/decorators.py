import orca

def group(groupname='Group1'):
    """
    Decorates functions that will be injected into other functions.
    """
    def decorator(func):
        step = func.__name__
        orcafunc_wrapper = orca.orca._STEPS[step]
        orcafunc_wrapper.groupname = groupname
        return func
    return decorator