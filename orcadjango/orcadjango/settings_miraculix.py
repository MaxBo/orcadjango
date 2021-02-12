from orcadjango.settings_pg import *

TIMEZONE = 'Europe/Berlin'
USE_TZ = True

ORCA_MODULES['default'].update({'path': 'extractiontools.steps.extract_data'})

ORCA_MODULES['available'].update({
    'extraction tools': {
        'path': 'extractiontools.steps.extract_data',
        'description': ('Collection of tools to extract data from the europe '
                        'database and to process it.'),
        'init': ['database', 'target_srid', 'project_area']
    }
})

ALLOWED_HOSTS = ['localhost',
                 'miraculix.ggr-planung.de']