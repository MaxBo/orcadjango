from django.db import models

class ScenarioList(models.Model):
    """ScenarioList"""
    name = models.TextField()


# Create your models here.
class Scenarios(models.Model):
    name = models.TextField()
    order = models.TextField(null=True)
    sclist = models.ForeignKey(ScenarioList, null=True,
                               on_delete=models.CASCADE,
                               related_name='scenarios')

    def __repr__(self):
        return f'{self.name} ({self.order})'


class Injectables(models.Model):
    name = models.TextField()
    scenario = models.ForeignKey(Scenarios,
                                 on_delete=models.CASCADE,
                                 null=True)
    value = models.TextField()
    changed = models.BooleanField(default=False)


class Steps(models.Model):
    name = models.TextField()
    scenario = models.ForeignKey(Scenarios, on_delete=models.CASCADE)
    started = models.DateTimeField()
    finished = models.DateTimeField()
    success = models.BooleanField(default=False)
    order = models.TextField(null=True)
