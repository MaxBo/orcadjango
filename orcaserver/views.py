from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .serializers import (ProjectSerializer, UserSerializer,
                          ScenarioSerializer, ModuleSerializer,
                          InjectableSerializer, StepSerializer,
                          ScenarioStepSerializer)
from .models import Project, Scenario, Injectable, Step, Run
from orcaserver.management import OrcaManager
from orcadjango.loggers import ScenarioHandler

def apply_injectables(scenario):
    orca_manager = OrcaManager(scenario.project.module)
    orca = orca_manager.get_instance(scenario.orca_id)
    inj_names = orca_manager.get_injectable_names()
    injectables = Injectable.objects.filter(name__in=inj_names,
                                            scenario=scenario)
    for inj in injectables:
        if inj.editable:
            orca.set_value(inj.name, inj.deserialized_value)


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

    @action(detail=True, methods=['post'])
    def run(self, request, **kwargs):
        scenario = Scenario.objects.get(id=kwargs.get('pk'))
        active_steps = Step.objects.filter(
            scenario=scenario, active=True).order_by('order')
        if len(active_steps) == 0:
            msg = 'No steps selected.'
            return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)
        manager = OrcaManager(scenario.project.module)
        orca = manager.get_instance(scenario.orca_id)
        if orca.is_running():
            msg = ('Orca is already running. Please wait for it to '
                   'finish or abort it.')
            return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)
        injectables_available = manager.get_injectable_names()
        steps_available = manager.get_step_names()
        for step in active_steps:
            if step.name not in steps_available:
                msg = ('There are steps selected that can not be found in the '
                       'module. Your project seems not to be up to date '
                       'with the module. Please remove those steps.')
                return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)
            meta = manager.get_step_meta(step.name)
            required = list(set(meta.get('injectables')) & set(injectables_available))
            inj_db = Injectable.objects.filter(name__in=required,
                                               scenario=scenario)
            if len(required) > len(inj_db):
                msg = ('There are steps selected that contain injectables that '
                       'can not be found. Your project seems not to be up to date '
                       'with the module. Please synchronize the parameters.')
                return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)

        active_steps.update(started=None, finished=None, success=False)
        apply_injectables(scenario)

        orca.clear_log_handlers()
        handler = ScenarioHandler(scenario)
        orca.add_log_handler(handler)

        run, created = Run.objects.get_or_create(scenario=scenario)
        run.run_by = request.user
        run.success = False
        run.started = timezone.now()
        run.finished =  None
        run.save()

        def on_success():
            run.success = True
            run.finished = timezone.now()
            print('success')
            run.save()
        def on_error():
            run.success = False
            run.finished = timezone.now()
            print('error')
            run.save()

        try:
            orca.start(steps=active_steps, on_success=on_success,
                       on_error=on_error)
        # ToDo: specific exceptions
        except Exception as e:
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Run started'}, status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def abort(request, *args, **kwargs):
        scenario = Scenario.objects.get(id=kwargs.get('pk'))
        manager = OrcaManager(scenario.project.module)
        orca = manager.get_instance(scenario.orca_id)
        if not orca.is_running:
            msg = 'Is not running'
            return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)
        orca.abort()
        return Response({'message': 'Run aborted'}, status.HTTP_200_OK)


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
        try:
            scenario = self.queryset.get(**kwargs)
        except Scenario.DoesNotExist:
            pass
        scenario.recreate_injectables()


class ModuleViewSet(viewsets.ViewSet):
    serializer_class = ModuleSerializer

    def list(self, request):
        available = settings.ORCA_MODULES.get('available', {})
        default_mod = OrcaManager.default_module
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


class StepViewSet(viewsets.ViewSet):
    serializer_class = StepSerializer

    def list(self, request):
        steps = []
        mod_p = request.query_params.get('module')
        module_names = [mod_p] if mod_p else [mod['path'] for mod in
             settings.ORCA_MODULES.get('available', {}).values()]
        for module in module_names:
            orca_manager = OrcaManager(module)
            names = orca_manager.get_step_names()
            for step in names:
                steps.append(orca_manager.get_step_meta(step))
        results = StepSerializer(steps, many=True)
        return Response(results.data)


class ScenarioStepViewSet(viewsets.ModelViewSet):
    queryset = Step.objects.all()
    serializer_class = ScenarioStepSerializer

    def get_queryset(self):
        return self.queryset.filter(scenario=self.kwargs['scenario_pk'])

    def create(self, request, *args, **kwargs):
        scenario = self.kwargs['scenario_pk']
        request.data['scenario'] = scenario
        return super().create(request, *args, **kwargs)