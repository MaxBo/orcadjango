import orca

def meta(**kwargs):
    """
    Function decorator (for orca.step and orca.injectable) with meta data
    interpreted by backend and/or UI

    Parameters
    ------------
        title: str, Optional, steps and injectables
            text to replace the otherwise parsed function name serving as the
            title of the step/injectable as displayed in the UI
        description: str, Optional, steps and injectables
            text to replace the otherwise parsed docstring serving as
            the description of the step/injectable as displayed in the UI
        group: str, Optional, steps and injectables
            group name of step/injectable for structuring in the UI
            steps/injectables with same group name are put together.
            if no group is given it will be put in a default group
        order: int, Optional, steps and injectables
            place of the step/injectable inside its group for ordering steps in
            the UI
        unique: bool, injectables only
            if True, injectable is validated to have a unique value across all
            values of the of the same injectable
        choices: list or function (orca.injectable), Optional, injectables only
            list of values that the user can select from in the UI when
            assigning a value/values for the injectable.
            can also be a function of another injectable that returns a list of
            values to choose from
        regex: text, Optional, injectables only
            restricts input values to be of a certain pattern,
            is evaluated by django RegexValidator
        regex_help: int, Optional, injectables only
            the description text for the regex to be displayed in the UI
        refresh: str, Optional, injectables only
            if "always" the backend will always recalculate the value of the
            injectable when it is queried or called.
            otherwise the value be only be calculated the first time it is
            queried (usually when loading the modules)
            other refresh options are not available yet
        hidden: bool, injectables only
            if True the UI will hide this injectable,
            usually for injectables that serve as inputs for steps/injectables
            but should not be changed by the user (e.g. precalculated choices or
            constants)
    """
    def decorator(func):
        name = func.__name__
        if not hasattr(orca, 'meta'):
            orca.meta = {}
        if name not in orca.meta:
            orca.meta[name] = {}
        for k, v in kwargs.items():
            orca.meta[name][k] = v
        return func
    return decorator
