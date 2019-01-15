from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('', views.get_python_file, name='index'),
    path('scenarios/', views.ScenariosView.as_view(), name='scenarios'),
    path('scenarios/create/', views.ScenariosView.create),
    path('injectables/', views.InjectablesView.as_view(), name='injectables'),
    path('injectables/<str:name>/', views.InjectableView.as_view(),
         name='injectable'),
    path('steps/', views.StepsView.as_view(), name='steps'),
    path('steps/list/', views.StepsView.list)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
