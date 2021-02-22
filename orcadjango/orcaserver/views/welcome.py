
from django.views.generic import FormView
from django.contrib.auth.views import LoginView

from orcaserver.views import ProjectMixin


class WelcomeView(ProjectMixin, LoginView):
    template_name = 'orcaserver/index.html'

    def get_context_data(self, **kwargs):
        kwargs['left_columns'] = 2
        kwargs['center_columns'] = 5
        kwargs['right_columns'] = 2
        return kwargs

