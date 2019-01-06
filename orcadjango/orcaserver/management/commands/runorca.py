from django.core.management.commands.runserver import Command as BaseCommand


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
        __import__(python_module)
        return super().execute(*args, **options)