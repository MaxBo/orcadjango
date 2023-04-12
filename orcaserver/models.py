from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone


class NameModel(models.Model):
    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Project(NameModel):
    name = models.TextField()
    description = models.TextField(blank=True)
    module = models.TextField(default='')
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    code = models.TextField(blank=True, default='')
    archived = models.BooleanField(default=False)
    created = models.DateTimeField(null=True)
    # ToDo: saved as plain text, maybe custom field here so that you don't need
    # to dump/load outside
    init = models.TextField(default='{}')

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.created = timezone.now()
        return super().save(*args, **kwargs)



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