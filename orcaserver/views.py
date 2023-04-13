from rest_framework import viewsets
from rest_framework.response import Response
from django.contrib.auth.models import User

from .serializers import (ProjectSerializer, UserSerializer,
                          ScenarioSerializer, ModuleSerializer)
from .models import Project, Scenario
from .utils import ProjectMixin
from django.conf import settings
from orcaserver.management import OrcaManager


class ProjectViewSet(ProjectMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        module = self.request.query_params.get('module')
        queryset = Project.objects.filter(module=module) if module is not None \
            else self.queryset
        return queryset.order_by('name')


class ScenarioViewSet(ProjectMixin, viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == "current":
            return self.request.user

        return super().get_object()


class ModuleViewSet(viewsets.ViewSet):
    serializer_class = ModuleSerializer

    def list(self, request):
        available = settings.ORCA_MODULES.get('available', {})
        default_mod = OrcaManager().default_module
        modules = []
        for k, v in available.items():
            path = v.get('path')
            mod = {
                'name': k,
                'path': path,
                'description': v.get('description', ''),
                'default': path == default_mod,
                'init': v.get('init'),
            }
            data_url = v.get('data_url', {})
            mod['data'] = {
                'name': data_url.get('name'),
                'href': data_url.get('href'),
                'url': data_url.get('url'),
                'text': v.get('data_text'),
            }
            modules.append(mod)
        results = ModuleSerializer(modules, many=True)
        return Response(results.data)