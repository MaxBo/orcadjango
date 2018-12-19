from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # ex: /orca/injectables/
    path('injectables/', views.injectables, name='injectables'),
    path('injectables/<str:name>/', views.injectable,
         name='injectable'),
]