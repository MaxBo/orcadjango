from rest_framework import serializers
from django.contrib.auth.models import User

from orcaserver.management import OrcaManager
from .models import Project, Profile, Scenario, Injectable
from .injectables import OrcaTypeMap
import json


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
            instance.module = OrcaManager().default_module
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


class ModuleSerializer(serializers.Serializer):
    name = serializers.CharField()
    path = serializers.CharField()
    description = serializers.CharField()
    default = serializers.BooleanField()
    data = ModuleDataSerializer()
    init = serializers.ListSerializer(child=serializers.CharField())


class InjectableSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    editable = serializers.SerializerMethodField()
    group = serializers.CharField(source='meta.group')

    class Meta:
        model = Injectable
        fields = ('id', 'name', 'group', 'scenario', 'value', 'datatype',
                  'parents', 'description', 'editable')
        read_only_fields = ('scenario', 'parents', 'datatype', 'name',
                            'description', 'editable', 'group')

    def get_description(self, obj):
        return obj.meta.get('docstring', '').replace('\n', '<br>')

    def get_editable(self, obj):
        if obj.parents:
            return False
        conv = OrcaTypeMap.get(obj.data_class)
        # only data types with an implemented converter should be changable
        # via UI, the default converter has no datatype
        if not conv.data_type:
            return False
        return True


    #@property
    #def can_be_changed(self):
        #if self.parent_injectable_values:
            #return False
        #conv = OrcaTypeMap.get(self.data_class)
        ## only data types with an implemented converter should be changable
        ## via UI, the default converter has no datatype
        #if not conv.data_type:
            #return False
        #return True


