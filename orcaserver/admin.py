from django.contrib import admin
from .injectables import Injectable
from .models import Scenario, Project


class ProjectAdmin(admin.ModelAdmin):
    exclude = ('module',)

admin.site.register(Project, ProjectAdmin)
admin.site.register(Scenario)
admin.site.register(Injectable)
