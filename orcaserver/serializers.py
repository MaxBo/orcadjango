from rest_framework import serializers
from django.contrib.auth.models import User
from collections import OrderedDict
import re
import json
from django.core.validators import RegexValidator
from rest_framework.serializers import ValidationError
from django.core.exceptions import ValidationError as CoreValidationError
from django.utils import timezone

from orcaserver.orca import OrcaManager
from .models import (Project, Profile, Scenario, Injectable, Step, Run,
                     Module, LogEntry, SiteSetting, Avatar)
from .injectables import OrcaTypeMap
import re

DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"


class AvatarSerializer(serializers.ModelSerializer):
    #users = serializers.ListField(source='profile_set__user_id')
    users = serializers.SerializerMethodField()

    class Meta:
        model = Avatar
        fields = ('id', 'image', 'name', 'users')

    def get_users(self, obj):
        return obj.profile_set.values_list('user_id', flat=True)


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ('color', 'avatar', 'show_backgrounds')
        optional_fields = ('show_backgrounds', )


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

    def to_representation(self, obj):
        if not hasattr(obj, 'profile') or not obj.profile:
            Profile.objects.create(user=obj)
        return super().to_representation(obj)

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance = super().create(validated_data)
        profile = instance.profile
        for k, v in profile_data.items():
            setattr(profile, k, v)
        profile.save()
        return instance

    def update(self, obj, validated_data):
        # ToDo: return permission error or move to view permissions
        user = self.context['request'].user
        if not user or user.id != obj.id and not user.is_superuser:
            return obj
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        if profile_data:
            if not hasattr(obj, 'profile') and not obj.profile:
                profile = Profile.objects.create(user=obj)
            profile = ProfileSerializer().update(obj.profile, profile_data)
        profile.save()
        obj = super().update(obj, validated_data)
        if password:
            obj.set_password(password)
            obj.save()
        return obj


class ProjectInjectablesSerializerField(serializers.Field):

    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        super().__init__(**kwargs)

    def to_representation(self, obj):
        orca_manager = OrcaManager(obj.module)
        module = obj._module
        if not module:
            return []
        init_names = obj._module.init_injectables
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

def validate_unique_inj(inj_name: str, value, project_id: int = None):
    '''validate if given value of injectable is not existing in other projects
    than the passed one
    raises ValidationError if it does and therefore is not unique'''
    same_val_inj = Injectable.objects.filter(
        name=inj_name, value=value)
    if project_id is not None:
        same_val_inj = same_val_inj.exclude(scenario__project=project_id)
    if same_val_inj.count():
        # has to be unique so it only can be exactly one other project
        # but list all projects anyway to be safe
        project_names = ', '.join(
            f'"{pn}"' for pn in same_val_inj.values_list(
                'scenario__project__name', flat=True).distinct())
        raise ValidationError({inj_name: f'Value has to be unique. "{value}" '
                              'is already used in project '
                              f'{project_names}.'})


class ProjectSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    injectables = ProjectInjectablesSerializerField(required=False)
    scenario_count = serializers.IntegerField(source='scenario_set.count',
                                              read_only=True)

    class Meta:
        model = Project
        fields =  ('id', 'name', 'description', 'module', 'code', 'user',
                   'archived', 'created', 'injectables', 'scenario_count')
        optional_fields = ('module', 'code', 'user', 'archived', 'created')

    def create(self, validated_data):
        module_path = validated_data.get('module')
        if not module_path:
            raise ValidationError('module missing')
        self.__validate_inj(module_path, validated_data)
        instance = super().create(validated_data)
        if not validated_data.get('created'):
            instance.created = timezone.now()
            instance.save()
        return instance

    def update(self, obj, validated_data):
        self.__validate_inj(obj.module, validated_data, project=obj)
        return super().update(obj, validated_data)

    def __validate_inj(self, module_path, validated_data, project=None):
        init = validated_data.get('init')
        if not init:
            return
        # it is kind of stupid to do this here, but there is no other
        # place (e.g. serializer field) where we have all information needed to
        # validate the uniqueness of injectables throught the projects,
        # so we have to deserialize the data again and catch the injectable
        # meta data in an unconvenient way
        inj_data = json.loads(init)
        orca_manager = OrcaManager(module_path)
        for inj_name, value in inj_data.items():
            meta = orca_manager.get_injectable_meta(inj_name)
            if meta.get('unique'):
                validate_unique_inj(inj_name, value,
                                    project_id=project.id if project else None)
            if meta.get('regex'):
                regex = meta.get('regex')
                regex_validator = RegexValidator(
                    regex, meta.get('regex_help', regex))
                try:
                    regex_validator(value)
                except CoreValidationError as e:
                    raise ValidationError(dict([(inj_name, str(e))]))


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
    timestamp = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    class Meta:
        model = LogEntry
        fields = ('scenario', 'message', 'timestamp', 'level', 'status')


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
    scope = serializers.SerializerMethodField()
    editable_keys = serializers.SerializerMethodField()
    group = serializers.CharField(source='meta.group', required=False,
                                  allow_blank=True)
    order = serializers.IntegerField(source='meta.order', required=False)
    unique = serializers.CharField(source='meta.unique', required=False,
                                   allow_blank=True)
    title = serializers.CharField(source='meta.title', required=False,
                                  allow_blank=True)
    regex_help = serializers.SerializerMethodField()
    value = serializers.JSONField(source='serialized_value')

    def get_choices(self, obj):
        return obj.meta.get('choices')

    def get_description(self, obj):
        return obj.meta.get('docstring', '').strip().replace('\n', ' ')#, '<br>')

    def get_regex_help(self, obj):
        return obj.meta.get('regex_help', '').strip().replace('\n', ' ')

    def get_scope(self, obj):
        return obj.meta.get('scope', 'global')

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

    def get_editable_keys(self, obj):
        return obj.meta.get('editable_keys', False)

    def update(self, obj, validated_data):
        value = validated_data.get('value')
        if obj.meta.get('unique') and value is not None:
            validate_unique_inj(obj.name, value, project_id=obj.scenario.project.id)
        return super().update(obj, validated_data)


class ScenarioInjectableSerializer(InjectableSerializer,
                                   serializers.ModelSerializer):
    '''injectables with values from database for a specific scenario'''

    class Meta:
        model = Injectable
        fields = ('id', 'name', 'title', 'group', 'order', 'scenario', 'value', 'multi', 'scope',
                  'datatype', 'editable_keys', 'parents', 'description', 'editable', 'choices',
                  'unique', 'regex_help')
        read_only_fields = ('scenario', 'parents', 'name', 'editable',
                            'choices', 'unique', 'title', 'regex_help')

    def update(self, instance, validated_data):
        if 'serialized_value' in validated_data:
            serialized_value = validated_data.pop('serialized_value')
            conv = OrcaTypeMap.get(instance.data_class)
            validated_data['value'] = conv.to_str(serialized_value)
            # ToDo: validation here (can't be done in overwritten validate
            # function, instance not known there)
        return super().update(instance, validated_data)


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('name', 'title', 'path', 'description', 'init_injectables',
                  'preview_injectable', 'info_html', 'default')


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


class SiteSettingSerializer(serializers.ModelSerializer):
    ''''''

    class Meta:
        model = SiteSetting
        fields = ('title', 'contact_mail', 'logo', 'favicon',
                  'scenario_running_img', 'scenario_running_icon',
                  'scenario_success_img', 'scenario_success_icon',
                  'scenario_failed_img', 'scenario_failed_icon',
                  'primary_color', 'secondary_color',
                  'welcome_text', 'welcome_background_img',
                  'projects_background_img', 'scenarios_background_img',
                  'injectables_background_img', 'steps_background_img')