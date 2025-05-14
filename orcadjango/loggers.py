import logging
import json
import time
import channels.layers
try:
    # redis 4.*
    from redis.asyncio import RedisError
except ModuleNotFoundError:
    # redis 3.*
    from redis import RedisError
from redis.exceptions import ConnectionError as RedisConnectionError
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.utils import timezone
from django import db
import re

import logging
logger = logging.getLogger(__name__)

channel_layer = channels.layers.get_channel_layer()

IGNORE_MESSAGE_FILTER = ['^registering injectable', '^(start|finish): call function to provide injectable']

def clear_db_connections():
    for conn in db.connections.all():
        conn.close_if_unusable_or_obsolete()

def send(channel: str, message: str, log_type: str='log_message',
         status=None, **kwargs):
    rec = {
        'message': message,
        'type': log_type,
        'timestamp': time.strftime('%d.%m.%Y %H:%M:%S')
    }
    if status:
        rec['status'] = status
    rec.update(kwargs)

    async_to_sync(channel_layer.group_send)(channel, rec)


class WebSocketHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room = 'log'

    def emit(self, record):
        try:
            send(self.room, record.getMessage(), log_type='log_message',
                 level=record.levelname)
        except (RedisError, RedisConnectionError, OSError, RuntimeError) as e:
            logger.debug(e)


class ScenarioHandler(WebSocketHandler):
    def __init__(self, scenario, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario = scenario
        self.room = f'scenario_{scenario.id}'

    @staticmethod
    def _do_ignore(record) -> bool:
        message = record.getMessage()
        for expr in IGNORE_MESSAGE_FILTER:
            if re.search(expr, message):
                return True
        return False

    def emit(self, record):
        if self._do_ignore(record):
            return
        clear_db_connections()
        from orcaserver.models import LogEntry
        message = record.getMessage()
        status = getattr(record, 'status', {})
        LogEntry.objects.create(
            scenario_id=self.scenario.id,
            message=message,
            timestamp=timezone.now(),
            level=record.levelname,
            status=status
        )
        record.scenario = self.scenario.name
        try:
            send(self.room, message, log_type='log_message',
                 level=record.levelname, status=status)
        except (RedisError, RedisConnectionError, OSError, RuntimeError) as e:
            logger.debug(e)


class ScenarioLogConsumer(WebsocketConsumer):
    def connect(self):
        '''join room'''
        self.scenario_id = self.scope['url_route']['kwargs']['scenario_id']
        self.room_name = f'scenario_{self.scenario_id}'
        try:
            async_to_sync(self.channel_layer.group_add)(
                self.room_name,
                self.channel_name
            )
            self.accept()
        # redis is not up, what to do?
        except (RedisError, RedisConnectionError, OSError) as e:
            logger.debug(e)

    def disconnect(self, close_code):
        '''leave room'''
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name,
            self.channel_name
        )

    def log_message(self, event):
        '''send "log_message"'''
        try:
            self.send(text_data=json.dumps({
                'message': event['message'],
                'level': event.get('level'),
                'timestamp': event.get('timestamp'),
                'status': event.get('status')
            }))
        except (RedisError, OSError, RedisConnectionError) as e:
            logger.debug(e)
