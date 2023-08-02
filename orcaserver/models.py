from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import json
from django.core.validators import int_list_validator
from django.core.exceptions import ObjectDoesNotExist

from .injectables import OrcaTypeMap
from .management import OrcaManager


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
    description = models.TextField(blank=True)

    @property
    def orca_id(self):
        return f'scenario-{self.id}'

    def recreate_injectables(self, keep_values=False):
        '''
        function to create or reset injectables of scenario
        '''
        orca_manager = OrcaManager(self.project.module)
        inj_names = orca_manager.get_injectable_names()
        descriptors = {}
        for name in inj_names:
            descriptors[name] = orca_manager.get_injectable_meta(name)
        project = self.project
        init_values = json.loads(project.init)
        # create or reset injectables
        for name, desc in descriptors.items():
            if not desc or desc.get('hidden'):
                continue
            inj, created = Injectable.objects.get_or_create(name=name,
                                                            scenario=self)
            value = init_values.get(name)
            if not value:
                conv = OrcaTypeMap.get(desc['data_class'])
                value = conv.to_str(desc.get('default'))
            if created or not keep_values:
                inj.value = value
            inj.datatype = desc['datatype']
            inj.data_class = desc['data_class']
            inj.save()
        # add parent injectable ids
        for name, desc in descriptors.items():
            if not desc or desc.get('hidden'):
                continue
            parent_injectables = []
            inj = self.injectable_set.get(name=name)
            for parameter in desc.get('parameters', []):
                try:
                    parent_inj = self.injectable_set.get(name=parameter)
                    parent_injectables.append(parent_inj.pk)
                except Injectable.DoesNotExist:
                    pass
                    #orca.logger.warn(f'Injectable {parameter} '
                                     #f'not found in scenario {inj.scenario.name}')
            inj.parent_injectables = str(parent_injectables)
            inj.save()


class Injectable(NameModel):
    name = models.TextField()
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True)
    value = models.TextField(null=True)
    datatype = models.TextField(null=True, blank=True)
    data_class = models.TextField(null=True, blank=True)
    parent_injectables = models.TextField(
        validators=[int_list_validator], default='[]')

    def __init__(self, *args, **kwargs):
        self.__meta = kwargs.pop('meta', None)
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f'{self.scenario} - {self.name}'

    @property
    def meta(self):
        '''buffered meta data for serialization'''
        if self.__meta:
            return self.__meta
        try:
            meta = OrcaManager(
                self.scenario.project.module).get_injectable_meta(self.name)
        # there is a rare possibility that scenario is deleted right at this moment.
        # injectable will follow but there is a short period where this might
        # cause an exception
        except ObjectDoesNotExist:
            meta = {'group': '', 'order': '',}
        self.__meta = meta
        return meta

    @property
    def parents(self):
        return json.loads(self.parent_injectables)

    @property
    def editable(self):
        if self.parents:
            return False
        conv = OrcaTypeMap.get(self.data_class)
        # only data types with an implemented converter should be changable
        # via UI, the default converter has no datatype
        if not conv.data_type:
            return False
        return True

    @property
    def derived_value(self):
        parents = self.parents
        if not parents:
            return self.value
        values = [Injectable.objects.get(id=p_id).deserialized_value
                  for p_id in parents]
        conv = OrcaTypeMap.get(self.data_class)
        value = OrcaManager(self.scenario.project.module).get_calculated_value(
            self.name, *values)
        return conv.to_str(value)

    # can unfortunatelly not be put into serializer field
    # (serialization usually happens first/last on request,
    # instance not known there)
    @property
    def deserialized_value(self):
        conv = OrcaTypeMap.get(self.data_class)
        value = conv.to_value(self.value)
        return value

    # can unfortunatelly not be put into custom (writable) serializer field
    @property
    def serialized_value(self):
        value = self.derived_value if self.parents else self.value
        if value is None:
            return
        # force flattening to 2D for geometries (very clunky)
        if self.datatype.lower() == 'geometry':
            conv = OrcaTypeMap.get(self.data_class)
            return conv.to_str(conv.to_value(value))
        try:
            ret = json.loads(value)
        except json.decoder.JSONDecodeError:
            try:
                ret = json.loads(value.replace("'",'"'))
            except json.decoder.JSONDecodeError:
                return value
        return ret


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