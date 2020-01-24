from django.contrib import admin
from django.contrib.gis import admin as geoadmin
from .models import Injectable, Scenario, Project, GeoProject


class GeoProjectAdmin(geoadmin.GeoModelAdmin):
    exclude = ('module',)


class ProjectAdmin(admin.ModelAdmin):
    exclude = ('module',)


geoadmin.site.register(GeoProject, GeoProjectAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Scenario)
admin.site.register(Injectable)
