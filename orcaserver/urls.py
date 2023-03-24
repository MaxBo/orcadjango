from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

#from django.contrib.admin.views.decorators import staff_member_required

from orcaserver import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='orcaserver/index.html')),
    path('settings/', login_required(views.SettingsView.as_view()),
         name='settings'),
    path('projects/', login_required(views.ProjectsView.as_view()),
         name='projects'),
    path('projects/change/<str:id>/',
         login_required(views.ProjectView.as_view())),
    path('projects/create/', login_required(views.ProjectView.as_view())),
    path('scenarios/', login_required(views.ScenariosView.as_view()),
         name='scenarios'),
    path('injectables/', login_required(views.InjectablesView.as_view()),
         name='injectables'),
    path('injectables/<str:name>/',
         login_required(views.InjectableView.as_view()),
         name='injectable'),
    path('status/', login_required(views.StatusView.as_view()), name='status'),
    path('logs/<str:id>/', login_required(views.LogsView.as_view()), name='logs'),
    #path('logs/detail/<str:id>/', login_required(views.LogsView.detail)),
    path('steps/', login_required(views.StepsView.as_view()), name='steps'),
    path('steps/run/', login_required(views.StepsView.run)),
    path('steps/list/', login_required(views.StepsListView.as_view())),
    path('steps/abort/<str:id>/', login_required(views.StepsView.abort)),
    path('steps/detail/<str:id>/', login_required(views.StepsView.detail)),
    path('status/detail/<str:id>/', login_required(views.StatusView.detail)),
    path('status/list/', login_required(views.StatusView.list)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)