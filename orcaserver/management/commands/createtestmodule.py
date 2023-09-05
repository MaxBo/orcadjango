from django.core.management.base import BaseCommand
from orcaserver.models import Module


class Command(BaseCommand):
    help = '(Re)create an entry for the test module '

    def handle(self, *args, **options):
        """handle the command"""
        try:
            m = Module.objects.get(name='dummy_orca_stuff')
            m.delete()
        except Module.DoesNotExist:
            pass
        Module.objects.create(
            name='dummy_orca_stuff',
            title='Orca Test Module',
            description='module used for testing',
            path='orcaserver.tests.dummy_orca_stuff',
            init_injectables=['inj_list', 'inj_dict'],
            default=True,
        )
