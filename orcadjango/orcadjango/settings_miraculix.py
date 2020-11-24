from orcadjango.settings_pg import *
import os

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

ORCA_MODULES['default'].update({'path': 'extractiontools.steps.extract_data'})

ORCA_MODULES['available'].update({
    'extraction tools': {
        'path': 'extractiontools.steps.extract_data',
        'description': ('collection of tools to extract data from the europe '
                        'database to a project database'),
        'init': ['database', 'target_srid', 'bbox_dict']
    }
})

ALLOWED_HOSTS = ['localhost',
                 'miraculix.ggr-planung.de']