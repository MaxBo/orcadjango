from rest_framework import routers

from .views import ProjectViewSet

router = routers.SimpleRouter()
router.register(r'projects', ProjectViewSet, basename='projects')

urlpatterns = router.urls