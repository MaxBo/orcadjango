from django.urls import path

from . import views

urlpatterns = [
    path('', views.get_python_file, name='index'),
    path('scenarios/', views.ScenariosView.as_view(), name='scenarios'),
    path('scenarios/create/', views.ScenariosView.create),
    path('injectables/', views.InjectablesView.as_view(), name='injectables'),
    path('injectables/<str:name>/', views.InjectableView.as_view(),
         name='injectable'),
    path('steps/', views.StepsView.as_view(), name='steps')
]
