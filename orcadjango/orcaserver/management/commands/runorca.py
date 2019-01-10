from django.core.management.commands.runserver import Command as BaseCommand
import orca

def load_module(module):
    orca.clear_all()
    __import__(module)
    orca._python_module = module
    orca._injectable_backup = {}
    for inj in orca.list_injectables():
        orca._injectable_backup[inj] = orca.get_injectable(inj)


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
