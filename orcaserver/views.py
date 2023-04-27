from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User

from .serializers import (ProjectSerializer, UserSerializer,
                          ScenarioSerializer, ModuleSerializer,
                          InjectableSerializer)
from .models import Project, Scenario, Injectable
from django.conf import settings
from orcaserver.management import OrcaManager


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        module = self.request.query_params.get('module')
        queryset = self.queryset.filter(module=module) if module is not None \
            else self.queryset
        return queryset.order_by('name')


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer

    def get_queryset(self):
        project = self.request.query_params.get('project')
        queryset = self.queryset.filter(project=project) if project is not None \
            else self.queryset
        return queryset.order_by('name')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk == "current":
            return self.request.user
        return super().get_object()


class InjectableViewSet(viewsets.ModelViewSet):
    queryset = Injectable.objects.all()
    serializer_class = InjectableSerializer

    def get_queryset(self):
        return self.queryset.filter(scenario=self.kwargs['scenario_pk'])

    @action(methods=['POST'], detail=False)
    def reset(self, request, **kwargs):
        """
        route to disaggregate the population to the raster cells
        """
        try:
            scenario = self.queryset.get(**kwargs)
        except Scenario.DoesNotExist:
            pass
        scenario.recreate_injectables()


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