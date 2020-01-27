from django.urls import re_path
from wslog import models

websocket_urlpatterns = [
    re_path(r'ws/log/(?P<room_name>\w+)/$', models.LogConsumer),
]