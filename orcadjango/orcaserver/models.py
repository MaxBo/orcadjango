from django.db import models
from django.contrib.gis.db.models import MultiPolygonField


class NameModel(models.Model):
    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Project(NameModel):
    name = models.TextField()
    description = models.TextField()
    module = models.TextField(default='')


class GeoProject(Project):
    srid = models.IntegerField()
    bbox = MultiPolygonField()


class Scenario(NameModel):
    """Scenario"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.TextField()


class Injectable(NameModel):
    name = models.TextField()
    scenario = models.ForeignKey(Scenario,
                                 on_delete=models.CASCADE,
                                 null=True)
    value = models.TextField(null=True)
    changed = models.BooleanField(default=False)
    can_be_changed = models.BooleanField(default=True)
    docstring = models.TextField(null=True, blank=True)
    module = models.TextField(null=True, blank=True)
    groupname = models.TextField(null=False, blank=False, default='')
    order = models.IntegerField(null=False, default=1)

    def __str__(self):
        return f'{self.scenario} - {self.name}'


class Step(NameModel):
    name = models.TextField()
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    started = models.DateTimeField(null=True)
    finished = models.DateTimeField(null=True)
    success = models.BooleanField(default=False)
    order = models.IntegerField(null=True)
    active = models.BooleanField(default=True)
    docstring = models.TextField(null=True, blank=True)
