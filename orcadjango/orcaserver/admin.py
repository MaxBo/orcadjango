from django.contrib import admin
from .models import Injectable, Scenario, Project


class ProjectAdmin(admin.ModelAdmin):
    exclude = ('module',)

admin.site.register(Project, ProjectAdmin)
admin.site.register(Scenario)
admin.site.register(Injectable)
