from rest_framework import viewsets
from rest_framework.decorators import action
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext as _

from .serializers import (ProjectSerializer, UserSerializer,
                          ScenarioSerializer, ModuleSerializer,
                          ScenarioInjectableSerializer, StepSerializer,
                          ScenarioStepSerializer, InjectableSerializer,
                          ScenarioLogSerializer, SiteSettingSerializer,
                          AvatarSerializer)
from .models import (Project, Scenario, Injectable, Step, Run, LogEntry,
                     SiteSetting, Module, Avatar)
from orcaserver.orca import OrcaManager
from orcadjango.loggers import ScenarioHandler
from .injectables import OrcaTypeMap


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
            msg = _('No steps selected.')
            return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)
        manager = OrcaManager(scenario.project.module)
        orca = manager.get_instance(scenario.orca_id)
        if orca.is_running():
            msg = _('Orca is already running. Please wait for it to '
                   'finish or abort it.')
            return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)
        injectables_available = manager.get_injectable_names()
        steps_available = manager.get_step_names()
        for step in active_steps:
            if step.name not in steps_available:
                msg = _(f'The step "{step.name}"steps can not be found in the '
                       'module definition. Your project seems not to be up to '
                       'date with the module. Please remove this step.')
                return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)
            if step.name not in orca.orca._STEPS.keys():
                msg = _(f'The step "{step.name}" can not be found in the module'
                       '. The module definition is not in line with the '
                       'available orca scripts. Please contact your admin.')
                return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)
            meta = manager.get_step_meta(step.name)
            required = list(set(meta.get('injectables')) & set(injectables_available))
            required = [r for r in required
                        if not manager.get_injectable_meta(r).get(
                            'hidden', False)]
            inj_db = Injectable.objects.filter(name__in=required,
                                               scenario=scenario)
            if len(required) > len(inj_db):
                msg = _('There are steps selected that contain injectables that '
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
            run.save()
        def on_error():
            run.success = False
            run.finished = timezone.now()
            run.save()

        try:
            orca.start(steps=active_steps, on_success=on_success,
                       on_error=on_error)
        # ToDo: specific exceptions
        except Exception as e:
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)
        return Response({'message': _('Run started')}, status.HTTP_202_ACCEPTED)

    @action(methods=['POST'], detail=True)
    def reset(self, request, **kwargs):
        scenario = self.queryset.get(**kwargs)
        scenario.recreate_injectables(keep_values=False)
        return Response({'message': _('Injectables reset')}, status.HTTP_200_OK)

    @action(methods=['POST'], detail=True)
    def synch(self, request, **kwargs):
        scenario = self.queryset.get(**kwargs)
        scenario.recreate_injectables(keep_values=True)
        return Response({'message': _('Injectables synchronized')},
                        status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def abort(request, *args, **kwargs):
        scenario = Scenario.objects.get(id=kwargs.get('pk'))
        manager = OrcaManager(scenario.project.module)
        orca = manager.get_instance(scenario.orca_id)
        if not orca.is_running:
            msg = _('Orca is not running')
            return Response({'message': msg}, status.HTTP_400_BAD_REQUEST)
        orca.abort()
        return Response({'message': _('Run aborted')}, status.HTTP_200_OK)


class AvatarViewSet(viewsets.ModelViewSet):
    queryset = Avatar.objects.all()
    serializer_class = AvatarSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk == "current":
            return self.request.user
        return super().get_object()


class InjectableViewSet(viewsets.ViewSet):
    serializer_class = InjectableSerializer

    def list(self, request, **kwargs):
        injectables = []
        module_name = kwargs['module_pk']
        module = Module.objects.get(name=module_name)
        orca_manager = OrcaManager(module.path)
        names = orca_manager.get_injectable_names(hidden=False)
        for inj in names:
            meta = orca_manager.get_injectable_meta(inj)
            # that's a little weird, but we create injectables to be able
            # to use the same functions as in scenario injectable serialization
            data_class = meta.get('data_class')
            conv = OrcaTypeMap.get(data_class)
            value = conv.to_str(meta.get('default'))
            injectable = Injectable(
                name=inj,
                value=value,
                meta=meta,
                data_class=data_class,
                datatype=meta.get('datatype'),
            )
            injectables.append(injectable)
        results = InjectableSerializer(injectables, many=True)
        return Response(results.data)


class ScenarioInjectableViewSet(viewsets.ModelViewSet):
    queryset = Injectable.objects.all()
    serializer_class = ScenarioInjectableSerializer

    def get_queryset(self):
        scenario = Scenario.objects.get(id=self.kwargs['scenario_pk'])
        queryset = self.queryset.filter(scenario=scenario)
        orca_manager = OrcaManager(scenario.project.module)
        apply_injectables(scenario)
        mod_injs = orca_manager.get_injectable_names(hidden=False)
        scen_injs = [i.name for i in queryset]
        if (set(mod_injs) != set(scen_injs)):
            scenario.recreate_injectables(keep_values=True)
            queryset = self.queryset.filter(scenario=scenario)
        return queryset


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer


class StepViewSet(viewsets.ViewSet):
    serializer_class = StepSerializer

    def list(self, request, **kwargs):
        steps = []
        module_name = kwargs['module_pk']
        module = Module.objects.get(name=module_name)
        orca_manager = OrcaManager(module.path)
        if not module:
            return Response({})
        orca_manager = OrcaManager(module.path)
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


class ScenarioLogViewSet(viewsets.ModelViewSet):
    queryset = LogEntry.objects.all()
    serializer_class = ScenarioLogSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(scenario=self.kwargs['scenario_pk'])
        level = self.request.query_params.get('level')
        n_last = self.request.query_params.get('n_last')
        # only possible options: DEBUG or INFO (DEBUG is everything anyway)
        if level == 'INFO':
            queryset = queryset.filter(level__in=['INFO', 'ERROR'])
        if n_last is not None:
            queryset = queryset.order_by('-timestamp')[:int(n_last)][::-1]
        else:
            queryset = queryset.order_by('timestamp')
        return queryset


class SingletonViewSet(viewsets.ModelViewSet):
    model_class = None

    def retrieve(self, request, *args, **kwargs):
        instance = self.model_class.load()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.model_class.load()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class SiteSettingViewSet(SingletonViewSet):
    queryset = SiteSetting.objects.all()
    model_class = SiteSetting
    serializer_class = SiteSettingSerializer
    permission_classes = []