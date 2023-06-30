import logging
import json
import time
#import channels.layers
#try:
    ## redis 4.*
    #from redis.asyncio import RedisError
#except ModuleNotFoundError:
    ## redis 3.*
    #from redis import RedisError
#from redis.exceptions import ConnectionError as RedisConnectionError
#from asgiref.sync import async_to_sync
#from channels.generic.websocket import AsyncWebsocketConsumer
#from django.utils import timezone

#import logging
#logger = logging.getLogger(__name__)


#def send(channel: str, message: str, log_type: str='log_message',
         #status={}, **kwargs):
    #rec = {
        #'message': message,
        #'type': log_type,
        #'timestamp': time.strftime('%d.%m.%Y %H:%M:%S'),
        #'status': status,
    #}
    #rec.update(kwargs)
    #channel_layer = channels.layers.get_channel_layer()
    #async_to_sync(channel_layer.group_send)(channel, rec)


#class WebSocketHandler(logging.StreamHandler):
    #def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)
        #self.setFormatter(logging.Formatter(
            #f'%(asctime)s,%(msecs)03d - %(message)s',
            #'%d.%m.%Y %H:%M:%S'))
        #self.room = 'log'

    #def emit(self, record):
        #status = getattr(record, 'status', {})
        #try:
            #send(self.room, record.getMessage(), log_type='log_message',
                 #level=record.levelname, status=status)
        #except (RedisError, RedisConnectionError, OSError, RuntimeError) as e:
            #logger.debug(e)


#class ScenarioHandler(WebSocketHandler):
    #def __init__(self, scenario, *args, **kwargs):
        #super().__init__(*args, **kwargs)
        #self.scenario_id = scenario.id
        #self.room = f'scenario_{scenario.id}'
        #self.setFormatter(logging.Formatter(
            #f'%(asctime)s,%(msecs)03d {scenario.name} - %(message)s',
            #'%d.%m.%Y %H:%M:%S'))

    #def emit(self, record):
        #from orcaserver.models import LogEntry
        #LogEntry.objects.create(
            #scenario_id=self.scenario_id,
            #message=record.getMessage(),
            #timestamp=timezone.now(),
            #level=record.levelname
        #)
        #super().emit(record)


#class ScenarioLogConsumer(AsyncWebsocketConsumer):
    #async def connect(self):
        #'''join room'''
        #self.scenario_id = self.scope['url_route']['kwargs']['scenario_id']
        #self.room_name = f'scenario_{self.scenario_id}'
        #try:
            #await self.channel_layer.group_add(
                    #self.room_name,
                    #self.channel_name
                #)

            #await self.accept()
        ## redis is not up, what to do?
        #except (RedisError, RedisConnectionError, OSError) as e:
            #logger.debug(e)

    #async def disconnect(self, close_code):
        #'''leave room'''
        #await self.channel_layer.group_discard(
            #self.room_name,
            #self.channel_name
        #)

    #async def log_message(self, event):
        #'''send "log_message"'''
        #try:
            #await self.send(text_data=json.dumps({
                #'message': event['message'],
                #'level': event.get('level'),
                #'timestamp': event.get('timestamp'),
                #'status': event.get('status')
            #}))
        #except (RedisError, OSError, RedisConnectionError) as e:
            #logger.debug(e)


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

import logging
logger = logging.getLogger(__name__)

channel_layer = channels.layers.get_channel_layer()

def send(channel: str, message: str, log_type: str='log_message',
         status={}, **kwargs):
    rec = {
        'message': message,
        'type': log_type,
        'timestamp': time.strftime('%d.%m.%Y %H:%M:%S'),
        'status': status,
    }
    rec.update(kwargs)

    async_to_sync(channel_layer.group_send)(channel, rec)


class WebSocketHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFormatter(logging.Formatter(
            f'%(asctime)s,%(msecs)03d - %(message)s',
            '%d.%m.%Y %H:%M:%S'))
        self.room = 'log'

    def emit(self, record):
        status = getattr(record, 'status', {})
        try:
            send(self.room, record.getMessage(), log_type='log_message',
                 level=record.levelname, status=status)
        except (RedisError, RedisConnectionError, OSError, RuntimeError) as e:
            logger.debug(e)


class ScenarioHandler(WebSocketHandler):
    def __init__(self, scenario, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_id = scenario.id
        self.room = f'scenario_{scenario.id}'
        self.setFormatter(logging.Formatter(
            f'%(asctime)s,%(msecs)03d {scenario.name} - %(message)s',
            '%d.%m.%Y %H:%M:%S'))

    def emit(self, record):
        from orcaserver.models import LogEntry
        LogEntry.objects.create(
            scenario_id=self.scenario_id,
            message=record.getMessage(),
            timestamp=timezone.now(),
            level=record.levelname
        )
        super().emit(record)


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
