from rest_framework import serializers
from django.contrib.auth.models import User
from collections import OrderedDict
import re
import json
from django.conf import settings

from orcaserver.management import OrcaManager
from .models import Project, Profile, Scenario, Injectable, Step, Run, LogEntry
from .injectables import OrcaTypeMap

DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"


class ProfileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Profile
        fields = ('icon', 'color')


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'is_superuser', 'profile', 'password')

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        # manual parsing of profile
        # didn't get parsing of nested multiform data to work otherwise
        profile = OrderedDict()
        for k in data.keys():
            match = re.search(r'profile\[(.*?)\]', k)
            if not match:
                continue
            skey = match.group(1)
            profile[skey] = data[k]
        if profile:
            value['profile'] = profile
        return value

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance = super().create(validated_data)
        profile = instance.profile
        for k, v in profile_data.items():
            setattr(profile, k, v)
        profile.save()
        return instance

    def update(self, instance, validated_data):
        # ToDo: return permission error or move to view permissions
        user = self.context['request'].user
        if not user or user.id != instance.id and not user.is_superuser:
            return instance
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        if profile_data:
            if not instance.profile:
                profile = Profile.objects.create(user=instance)
            profile = ProfileSerializer().update(instance.profile, profile_data)
        profile.save()
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class ProjectInjectablesSerializerField(serializers.Field):

    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        super().__init__(**kwargs)

    def to_representation(self, obj):
        orca_manager = OrcaManager(obj.module)
        module = settings.ORCA_MODULES['available'].get(obj.module_name)
        if not module:
            return []
        init_names = module.get('init')
        init_values = json.loads(obj.init)
        injectables = []
        for inj_name in init_names:
            value = init_values.get(inj_name, '')
            meta = orca_manager.get_injectable_meta(inj_name)
            injectable = Injectable(
                name=inj_name,
                value=json.dumps(value) if not isinstance(value, str) else value,
                meta=meta,
                datatype=meta.get('datatype', ''),
                data_class=meta.get('data_class', '')
            )
            injectables.append(injectable)
        results = InjectableSerializer(injectables, many=True)
        return results.data

    def to_internal_value(self, data):
        serializer = InjectableSerializer(many=True)
        # this does not make a lot of sense, only renaming 'value' to
        # 'serialized_value' but i leave it in for now
        injectables = serializer.to_internal_value(data)
        init = {}
        for inj in injectables:
            init[inj['name']] = inj['serialized_value']
        return {'init': json.dumps(init)}

    #def run_validation(self, datay=empty):
        #return True


class ProjectSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%Y-%m-%d", read_only=True)
    injectables = ProjectInjectablesSerializerField(required=False)
    scenario_count = serializers.IntegerField(source='scenario_set.count',
                                              read_only=True)

    class Meta:
        model = Project
        fields =  ('id', 'name', 'description', 'module', 'code', 'user',
                   'archived', 'created', 'injectables', 'scenario_count')
        optional_fields = ('module', 'code', 'user', 'archived')

    def create(self, validated_data):
        instance = super().create(validated_data)
        if not instance.module:
            default_mod_path = settings.ORCA_MODULES['available']['path']
            instance.module = default_mod_path
            instance.save()
        return instance

    #def update(self, obj, validated_data):
        #super().update(obj, validated_data)

    #def update(self, obj, validated_data):
        #injectables = validated_data.pop('injectables')
        #init_values = self._inj_to_init(obj, injectables, update=True)

    #def _inj_to_init(self, obj, inj_data, update=True):
        #module = settings.ORCA_MODULES['available'].get(obj.module_name)
        #init_proj_values = json.loads(obj.init)
        #for i, name in enumerate(init_names):
            #val = obj.init
            #inj = inj_data


class ScenarioSerializer(serializers.ModelSerializer):
    last_run = serializers.SerializerMethodField()
    is_running = serializers.SerializerMethodField()

    class Meta:
        model = Scenario
        fields =  ('id', 'name', 'project', 'description', 'last_run',
                   'is_running')

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.recreate_injectables()
        return instance

    def get_last_run(self, obj):
        # actually atm there will only be one, just in case
        runs = Run.objects.filter(scenario=obj).order_by('finished')
        if not runs:
            return
        return RunSerializer(runs.last()).data

    def get_is_running(self, obj):
        return OrcaManager(obj.project.module).is_running(obj.orca_id)


class ScenarioLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = ('scenario', 'message', 'timestamp', 'level')


class RunSerializer(serializers.ModelSerializer):
    started = serializers.DateTimeField(format=DATETIME_FORMAT,
                                        required=False, read_only=True)
    finished = serializers.DateTimeField(format=DATETIME_FORMAT,
                                         required=False, read_only=True)
    class Meta:
        model = Run
        fields =  ('started', 'finished', 'success', 'run_by')


class InjectableSerializer(serializers.Serializer):
    '''computed injectables of the module'''
    name = serializers.CharField()
    description = serializers.SerializerMethodField()
    datatype = serializers.SerializerMethodField()
    multi = serializers.SerializerMethodField()
    choices = serializers.SerializerMethodField()
    group = serializers.CharField(source='meta.group')
    order = serializers.CharField(source='meta.order')
    value = serializers.JSONField(source='serialized_value')

    def get_choices(self, obj):
        return obj.meta.get('choices')

    def get_description(self, obj):
        return obj.meta.get('docstring', '').strip().replace('\n', ' ')#, '<br>')

    def get_datatype(self, obj):
        if 'list' in obj.datatype.lower():
            # find the type of list elements
            typ_groups = re.search(r'\[(.*?)\]', obj.datatype)
            if (typ_groups):
                return typ_groups.group(1)
        # we ignore the types and just assume {str: str} dicts
        if 'dict' in obj.datatype.lower():
            return 'dict'
        return obj.datatype.lower()

    def get_multi(self, obj):
        return 'list' in obj.datatype.lower()


class ScenarioInjectableSerializer(InjectableSerializer,
                                   serializers.ModelSerializer):
    '''injectables with values from database for a specific scenario'''

    class Meta:
        model = Injectable
        fields = ('id', 'name', 'group', 'order', 'scenario', 'value', 'multi',
                  'datatype', 'parents', 'description', 'editable', 'choices')
        read_only_fields = ('scenario', 'parents', 'name', 'editable',
                            'choices')

    def update(self, instance, validated_data):
        if 'serialized_value' in validated_data:
            serialized_value = validated_data.pop('serialized_value')
            conv = OrcaTypeMap.get(instance.data_class)
            validated_data['value'] = conv.to_str(serialized_value)
            # ToDo: validation here (can't be done in overwritten validate
            # function, instance not known there)
        return super().update(instance, validated_data)


class ModuleDataSerializer(serializers.Serializer):
    name = serializers.CharField()
    url = serializers.CharField()
    href = serializers.CharField()
    text = serializers.ListSerializer(child=serializers.CharField())


class ModuleSerializer(serializers.Serializer):
    name = serializers.CharField()
    title = serializers.CharField()
    path = serializers.CharField()
    description = serializers.CharField()
    default = serializers.BooleanField()
    data = ModuleDataSerializer()
    init = serializers.ListSerializer(child=serializers.CharField())


class StepSerializer(serializers.Serializer):
    name = serializers.CharField()
    title = serializers.CharField()
    group = serializers.CharField()
    description = serializers.SerializerMethodField()
    order = serializers.IntegerField()
    required = serializers.ListSerializer(child=serializers.CharField())
    injectables = serializers.ListSerializer(child=serializers.CharField())

    def get_description(self, obj):
        return obj.get('docstring', '').strip().replace('\n', ' ')#, '<br>')


class ScenarioStepSerializer(serializers.ModelSerializer):
    started = serializers.DateTimeField(format=DATETIME_FORMAT,
                                        required=False, read_only=True)
    finished = serializers.DateTimeField(format=DATETIME_FORMAT,
                                         required=False, read_only=True)
    class Meta:
        model = Step
        fields = ('id', 'name', 'scenario', 'started', 'finished',
                  'success', 'order', 'active')
        read_only_fields = ('started', 'finished', 'success')
        optional_fields = ('order', 'active')