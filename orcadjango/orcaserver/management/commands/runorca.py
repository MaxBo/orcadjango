from django.core.management.commands.runserver import Command as BaseCommand
import orca
import importlib


def load_module(module_name, module_set=None):
    if module_set is None:
        orca._python_module = module_name
        orca.clear_all()
        orca._injectable_backup = {}
        module_set = {module_name}
    module = importlib.import_module(module_name)
    importlib.reload(module)
    for inj in orca.list_injectables():
        orca._injectable_backup[inj] = orca.get_injectable(inj)

    if hasattr(module, '__parent_modules__'):
        for module_name in module.__parent_modules__:
            if not module_name in module_set:
                load_module(module_name, module_set)
                module_set.add(module_name)



class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--orca_python_module',
            help='python module that imports the '
            'orca steps,tables and injectables',
            default='orcaserver.tests.dummy_orca_stuff',
        )

    def execute(self, *args, **options):
        python_module = options.pop('orca_python_module')
        load_module(python_module)
        return super().execute(*args, **options)
