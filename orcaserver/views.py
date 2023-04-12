from rest_framework import viewsets

from django.contrib.auth.models import User

from .serializers import ProjectSerializer, UserSerializer
from .models import Project
from .utils import ProjectMixin


class ProjectViewSet(ProjectMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        module = self.get_module()
        if not module:
            return []
        return Project.objects.filter(
            module=self.get_module()).order_by('name')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == "current":
            return self.request.user

        return super().get_object()