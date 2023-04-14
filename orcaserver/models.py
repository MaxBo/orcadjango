from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


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


class Profile(models.Model):
    '''
    adds additional user information
    '''
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    icon = models.ImageField(null=True, blank=True)
    color = models.CharField(max_length=9, default='#FFFFFF')
    settings = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.user.username}'

    def delete(self, **kwargs):
        # delete user of profile
        user = self.user
        if user:
            user.delete()
        super().delete(**kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    '''auto create profiles for new users'''
    if created:
        Profile(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()