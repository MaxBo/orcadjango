from rest_framework import serializers
from django.contrib.auth.models import User
import re

from orcaserver.management import OrcaManager
from .models import Project, Profile, Scenario, Injectable, Step
from .injectables import OrcaTypeMap


class ProfileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Profile
        fields = ('icon', )


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'is_superuser', 'profile')

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance = super().create(validated_data)
        profile = instance.profile
        for k, v in profile_data.items():
            setattr(profile, k, v)
        profile.save()
        return instance

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        profile = instance.profile
        if not profile:
            profile = Profile(user=instance)
            instance.profile = profile
        for k, v in profile_data.items():
            setattr(profile, k, v)
        profile.save()
        return super().update(instance, validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%Y-%m-%d", read_only=True)

    class Meta:
        model = Project
        fields =  ('id', 'name', 'description', 'module', 'code', 'user',
                   'archived', 'created')
        optional_fields = ('module', 'code', 'user', 'archived')

    def create(self, validated_data):
        instance = super().create(validated_data)
        if not instance.module:
            instance.module = OrcaManager.default_module
            instance.save()
        return instance


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields =  ('id', 'name', 'project', 'description')

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.recreate_injectables()
        return instance


class ModuleDataSerializer(serializers.Serializer):
    name = serializers.CharField()
    url = serializers.CharField()
    href = serializers.CharField()
    text = serializers.ListSerializer(child=serializers.CharField())


class InjectableSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    datatype = serializers.SerializerMethodField()
    multi = serializers.SerializerMethodField()
    choices = serializers.SerializerMethodField()
    group = serializers.CharField(source='meta.group')
    order = serializers.CharField(source='meta.order')
    value = serializers.JSONField(source='serialized_value')

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

    def get_choices(self, obj):
        return obj.meta.get('choices')

    def get_description(self, obj):
        return obj.meta.get('docstring', '').strip().replace('\n', '<br>')

    def get_datatype(self, obj):
        if 'list' in obj.datatype.lower():
            # find the type of list elements
            typ_groups = re.search(r'\[(.*?)\]', obj.datatype)
            if (typ_groups):
                return typ_groups.group(1)
        # we ignore the types and just assume {str: str} dicts
        if 'dict' in obj.datatype.lower():
            return 'dict'
        return obj.datatype

    def get_multi(self, obj):
        return 'list' in obj.datatype.lower()


class ModuleSerializer(serializers.Serializer):
    name = serializers.CharField()
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

    def get_description(self, obj):
        return obj.get('docstring', '').strip().replace('\n', '<br>')


class ScenarioStepSerializer(serializers.ModelSerializer):

    class Meta:
        model = Step
        fields = ('id', 'name', 'scenario', 'started', 'finished',
                  'success', 'order', 'active')
        read_only_fields = ('started', 'finished', 'success')
        optional_fields = ('order', 'active')