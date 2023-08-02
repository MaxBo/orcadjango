from rest_framework_nested import routers
from django.urls import path, include
from orcaserver import views

router = routers.SimpleRouter()
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'projects', views.ProjectViewSet, basename='projects')
router.register(r'scenarios', views.ScenarioViewSet, basename='scenarios')
router.register(r'modules', views.ModuleViewSet, basename='modules')

module_router = routers.NestedSimpleRouter(router, r'modules',
                                           lookup='module')
module_router.register(r'injectables', views.InjectableViewSet,
                       basename='injectables')
module_router.register(r'steps', views.StepViewSet, basename='steps')

scen_router = routers.NestedSimpleRouter(router, r'scenarios',
                                         lookup='scenario')
scen_router.register(r'injectables', views.ScenarioInjectableViewSet,
                     basename='scenario_injectables')
scen_router.register(r'steps', views.ScenarioStepViewSet,
                     basename='scenario_steps')

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'', include(module_router.urls)),
    path(r'', include(scen_router.urls)),
]