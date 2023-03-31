from rest_framework import routers
from django.urls import path

from orcaserver import views

router = routers.SimpleRouter()
router.register(r'projects', views.ProjectViewSet, basename='projects')

rest_login_patterns = [
    path('csrf/', views.get_csrf, name='csrf'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('session/', views.session_view, name='session')
]

urlpatterns = router.urls + rest_login_patterns