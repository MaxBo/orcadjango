from django.contrib import admin
from django.contrib.gis import admin as geoadmin
from .models import Injectable, Scenario, Project, GeoProject

geoadmin.site.register(GeoProject, geoadmin.GeoModelAdmin)
admin.site.register(Project)
admin.site.register(Scenario)
admin.site.register(Injectable)
