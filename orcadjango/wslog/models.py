from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json


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