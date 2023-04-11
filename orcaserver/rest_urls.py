from rest_framework import routers

from orcaserver import views

router = routers.SimpleRouter()
router.register(r'projects', views.ProjectViewSet, basename='projects')
router.register(r'users', views.UserViewSet, basename='users')

urlpatterns = router.urls