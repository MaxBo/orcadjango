from rest_framework_nested import routers
from django.urls import path, include
from orcaserver import views

router = routers.SimpleRouter()
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'projects', views.ProjectViewSet, basename='projects')
router.register(r'scenarios', views.ScenarioViewSet)
router.register(r'modules', views.ModuleViewSet, basename='modules')
router.register(r'steps', views.StepViewSet, basename='steps')

scen_router = routers.NestedSimpleRouter(router, r'scenarios',
                                         lookup='scenario')
scen_router.register(r'injectables', views.InjectableViewSet,
                     basename='injectables')
scen_router.register(r'steps', views.ScenarioStepViewSet,
                     basename='scenariosteps')

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'', include(scen_router.urls)),
]