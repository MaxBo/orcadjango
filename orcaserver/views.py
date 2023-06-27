from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User

from .serializers import (ProjectSerializer, UserSerializer,
                          ScenarioSerializer, ModuleSerializer,
                          InjectableSerializer, StepSerializer,
                          ScenarioStepSerializer)
from .models import Project, Scenario, Injectable, Step
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

    @action(detail=True, methods=['post'])
    def run(self, request, **kwargs):
        scenario = Scenario.objects.get(id=kwargs.get('scenario_pk'))
        orca = scenario.get_orca()
        active_steps = Step.objects.filter(
            scenario=scenario, active=True).order_by('order')


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


    @classmethod
    def run(cls, request):
        scenario_id = request.session.get('scenario')
        if not scenario_id:
            return
        scenario_id = int(scenario_id)
        orca = manager.get(scenario_id, create=False)
        if not orca:
            return HttpResponse(status=400)
        scenario = Scenario.objects.get(id=scenario_id)

        active_steps = Step.objects.filter(
            scenario=scenario, active=True).order_by('order')
        if len(active_steps) == 0:
            orca.logger.error('No steps selected.')
            return HttpResponse(status=400)
        # check if all injectables are available
        injectables_available = orca.list_injectables()
        steps_available = orca.list_steps()
        for step in active_steps:
            if step.name not in steps_available:
                orca.logger.error(
                    'There are steps selected that can not be found in the '
                    'module. Your project seems not to be up to date '
                    'with the module. Please remove those steps.')
                return HttpResponse(status=400)
            func = orca.get_step(step.name)
            sig = signature(func._func)
            inj_parameters = sig.parameters
            required = list(set(inj_parameters) & set(injectables_available))
            inj_db = Injectable.objects.filter(name__in=required,
                                               scenario=scenario)
            if len(required) > len(inj_db):
                orca.logger.error(
                    'There are steps selected that contain injectables that '
                    'not be found. Your project seems not to be up to date '
                    'with the module.<br>Please synchronize the parameters '
                    '(parameters page).')
                return HttpResponse(status=400)
        for step in active_steps:
            step.started = None
            step.finished = None
            step.success = False
            step.save()
        apply_injectables(orca, scenario)
        if manager.is_running(scenario.id):
            orca.logger.error('Orca is already running. Please wait for it to '
                         'finish or abort it.')
            return HttpResponse(status=400)

        message = f'Running Steps for scenario "{scenario.name}"'
        orca.logger.info(message)

        run, created = Run.objects.get_or_create(scenario=scenario)
        run.run_by = request.user
        run.success = False
        run.started = timezone.now()
        run.finished =  None
        run.save()

        def on_success():
            run.success = True
            run.finished = timezone.now()
            run.save()
        def on_error():
            run.success = False
            run.finished = timezone.now()
            run.save()

        try:
            manager.start(scenario.id, steps=active_steps,
                          on_success=on_success, on_error=on_error)
        # ToDo: specific exceptions
        except Exception as e:
            orca.logger.error(str(e))
            return HttpResponse(status=400)
        return HttpResponse(status=200)

    @staticmethod
    def abort(request, *args, **kwargs):
        scenario_id = int(kwargs.get('id'))
        manager = OrcaManager()
        manager.abort(scenario_id)
        return HttpResponse(status=200)


class ScenarioStepViewSet(viewsets.ModelViewSet):
    queryset = Step.objects.all()
    serializer_class = ScenarioStepSerializer

    def get_queryset(self):
        return self.queryset.filter(scenario=self.kwargs['scenario_pk'])

    def create(self, request, *args, **kwargs):
        scenario = self.kwargs['scenario_pk']
        request.data['scenario'] = scenario
        return super().create(request, *args, **kwargs)