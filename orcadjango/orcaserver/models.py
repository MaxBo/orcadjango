from django.db import models


class NameModel(models.Model):
    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Scenario(NameModel):
    """Scenario"""
    name = models.TextField()


class Injectable(NameModel):
    name = models.TextField()
    scenario = models.ForeignKey(Scenario,
                                 on_delete=models.CASCADE,
                                 null=True)
    value = models.TextField()
    changed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.scenario} - {self.name}'


class Step(NameModel):
    name = models.TextField()
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    started = models.DateTimeField()
    finished = models.DateTimeField()
    success = models.BooleanField(default=False)
    order = models.TextField(null=True)
