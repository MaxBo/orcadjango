from django.contrib import admin


# Register your models here.
from .models import Injectables, ScenarioList, Scenarios


admin.site.register(Injectables)
admin.site.register(ScenarioList)
admin.site.register(Scenarios)
