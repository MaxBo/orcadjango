from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('injectables/', views.InjectablesView.as_view(), name='injectables'),
    path('injectables/<str:name>/', views.InjectableView.as_view(),
         name='injectable'),
]