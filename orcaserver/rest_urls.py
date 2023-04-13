from rest_framework import routers

from orcaserver import views

router = routers.SimpleRouter()
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'projects', views.ProjectViewSet, basename='projects')
router.register(r'scenarios', views.ScenarioViewSet, basename='scenarios')
router.register(r'modules', views.ModuleViewSet, basename='modules')

urlpatterns = router.urls