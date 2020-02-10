from orcaserver.views.steps import apply_injectables
from orcaserver.models import Scenario, Project
from django.conf import settings


def init_injectables():
    project = Project.objects.filter(module=settings.ORCA_MODULE).first()
    scenario = Scenario.objects.filter(project=project).first()
    apply_injectables(scenario)