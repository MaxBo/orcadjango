from django.contrib import admin
from .models import Scenario, Project, Profile, Injectable, SiteSetting, Module


class ProjectAdmin(admin.ModelAdmin):
    exclude = ('module',)

admin.site.register(Module)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Scenario)
admin.site.register(Injectable)
admin.site.register(Profile)
admin.site.register(SiteSetting)

try:
    SiteSetting.load()
except:
    pass