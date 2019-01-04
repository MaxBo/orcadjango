from django.contrib import admin
from django_sorting_field.utils import sort_by_order


# Register your models here.
from .models import Injectables, ScenarioList, Scenarios


admin.site.register(Injectables)
admin.site.register(ScenarioList)
admin.site.register(Scenarios)
