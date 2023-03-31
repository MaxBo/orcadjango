from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Project


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields =  ('id', 'name', 'description', 'module')
        optional_fields = ('module')