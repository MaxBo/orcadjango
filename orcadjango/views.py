from django.views.generic.base import TemplateView
from orcaserver.models import SiteSetting
from django.conf import settings


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_settings = SiteSetting.load()
        context['title'] = site_settings.title
        context['favicon'] = site_settings.favicon.url
        context.update(settings.ANGULAR_RESOURCES)
        return context
