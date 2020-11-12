import logging
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import channels.layers
from datetime import datetime

def send(channel, message, log_type='log_message'):
    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(channel, {
        'message': message,
        #'timestamp': datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y"),
        'type': log_type
    })


class OrcaChannelHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = 'log_orca'
        self.setFormatter(logging.Formatter('%(asctime)s %(message)s'))

    def emit(self, record):
        log_type = 'log_error' if record.levelname == 'ERROR' else 'log_message'
        send(self.group, self.format(record), log_type=log_type)


class ScenarioHandler(OrcaChannelHandler):
    def __init__(self, scenario, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = f'log_{scenario.id}'
        self.setFormatter(logging.Formatter(
            f'%(asctime)s {scenario.name} - %(message)s'))


class LogConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'log_{self.room_name}'
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def log_message(self, event):
        message = event['message']
        timestamp = event.get('timestamp')
        if timestamp:
            message = f'&lt;{timestamp}&gt; {message}'
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
        }))

    def log_error(self, event):
        message = event['message']
        timestamp = event.get('timestamp')
        if timestamp:
            message = f'&lt;{timestamp}&gt; {message}'
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'error': True
        }))