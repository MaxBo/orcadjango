from django.db import models
from django.conf import settings


class NameModel(models.Model):
    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Project(NameModel):
    name = models.TextField()
    description = models.TextField()
    module = models.TextField(default='')
    # ToDo: saved as plain text, maybe custom field here so that you don't need
    # to dump/load outside
    init = models.TextField(default='{}')


class Scenario(NameModel):
    """Scenario"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.TextField()


class Step(NameModel):
    name = models.TextField()
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    started = models.DateTimeField(null=True)
    finished = models.DateTimeField(null=True)
    success = models.BooleanField(default=False)
    order = models.IntegerField(null=True)
    active = models.BooleanField(default=True)


class LogEntry(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    level = models.TextField(default='INFO')
    timestamp = models.DateTimeField()


class Run(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    models.OneToOneField(Scenario, on_delete=models.CASCADE)
    started = models.DateTimeField(null=True)
    finished = models.DateTimeField(null=True)
    success = models.BooleanField(default=False)
    run_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.SET_NULL, null=True)
