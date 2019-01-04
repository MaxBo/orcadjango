from django.contrib import admin


# Register your models here.
from .models import Injectable, Scenario


admin.site.register(Injectable)
admin.site.register(Scenario)
