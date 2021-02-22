from orcadjango.settings_pg import *
import os

TIMEZONE = 'Europe/Berlin'
USE_TZ = True

ORCA_MODULES['default'].update({'path': 'extractiontools.steps.extract_data'})

ORCA_MODULES['available'].update({
    'Extraction Tools': {
        'path': 'extractiontools.steps.extract_data',
        'description': ('Collection of tools to extract data from a europe-wide '
                        'database and to process the extracted data.'),
        'init': ['database', 'target_srid', 'project_area'],
        'data_folder': '/opt/dockerfiles/...',
        'data_url': {
            'name': 'miraculix.ggr-planung.de/results',
            'url': f'https://{os.environ.get("APACHE_USER")}:'
            f'{os.environ.get("APACHE_PASS")}@miraculix.ggr-planung.de/results',
        },
        'data_text': [f'PostGIS host: {DB_HOST}',
                      f'PostGIS port: {DB_PORT}',
                      f'PostGIS user: {DB_USER}']
    }
})

ALLOWED_HOSTS = ['localhost',
                 'miraculix.ggr-planung.de']