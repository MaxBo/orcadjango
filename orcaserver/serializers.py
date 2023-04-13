from rest_framework import serializers
from django.contrib.auth.models import User

from orcaserver.management import OrcaManager
from .models import Project, Profile, Scenario


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
    class Meta:
        model = Project
        fields =  ('id', 'name', 'description', 'module', 'code', 'user',
                   'archived', 'created')
        optional_fields = ('module', 'code', 'user', 'archived')
        read_only_fields = ('created', )

    def create(self, validated_data):
        instance = super().create(validated_data)
        if not instance.module:
            instance.module = OrcaManager().default_module
            instance.save()
        return instance


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields =  ('id', 'name', 'project')


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