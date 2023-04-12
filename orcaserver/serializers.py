from rest_framework import serializers
from django.contrib.auth.models import User

from orcaserver.management import OrcaManager
from .models import Project


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'is_superuser')


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields =  ('id', 'name', 'description', 'module', 'code', 'user',
                   'archived', 'created')
        optional_fields = ('module', 'code', 'user', 'archived')
        read_only_fields = ('created', )

    def create(self, validated_data):
        instance = super().create(validated_data)
        module = self.context['request'].session.get(
            'module', OrcaManager().default_module)
        instance.module = module
        instance.save()
        return instance