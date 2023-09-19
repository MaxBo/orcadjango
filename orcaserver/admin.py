from django.contrib import admin
from .models import (Scenario, Project, Profile, Injectable, SiteSetting,
                     Module, Avatar)


class ProjectAdmin(admin.ModelAdmin):
    exclude = ('module',)

admin.site.register(Module)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Scenario)
admin.site.register(Injectable)
admin.site.register(Profile)
admin.site.register(SiteSetting)
admin.site.register(Avatar)

try:
    SiteSetting.load()
except:
    pass