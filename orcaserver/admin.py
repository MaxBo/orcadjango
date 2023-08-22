from django.contrib import admin
from .models import Scenario, Project, Profile, Injectable


class ProjectAdmin(admin.ModelAdmin):
    exclude = ('module',)

admin.site.register(Project, ProjectAdmin)
admin.site.register(Scenario)
admin.site.register(Injectable)
admin.site.register(Profile)
