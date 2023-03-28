from rest_framework import viewsets
from rest_framework import permissions

from .serializers import ProjectSerializer
from .models import Project
from .utils import ProjectMixin


class ProjectViewSet(ProjectMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = []

    def get_queryset(self):
        module = self.get_module()
        if not module:
            return []
        return Project.objects.filter(
            module=self.get_module()).order_by('name')