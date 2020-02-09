
import orca
import importlib


def load_module(module_name, module_set=None):
    if module_set is None:
        orca._python_module = module_name
        orca.clear_all()
        orca._injectable_backup = {}
        orca._injectable_function = {}
        module_set = {module_name}
    module = importlib.import_module(module_name)
    importlib.reload(module)
    for inj in orca.list_injectables():
        orca._injectable_function[inj] = orca.orca._INJECTABLES[inj]
        try:
            orca._injectable_backup[inj] = orca.get_injectable(inj)
        except Exception as e:
            orca._injectable_backup[inj] = repr(e)

    # reload the parent modules
    parent_modules = getattr(module, '__parent_modules__', [])
    for module_name in parent_modules:
        #  if the are not reloaded yet
        if not module_name in module_set:
            load_module(module_name, module_set)
            module_set.add(module_name)
