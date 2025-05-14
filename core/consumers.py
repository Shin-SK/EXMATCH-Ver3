# core/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = f"dm_{self.scope['url_route']['kwargs']['user_id']}_{self.scope['user'].id}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # DB 保存など
        await self.channel_layer.group_send(
            self.room_name,
            {"type": "chat.message", "sender": self.scope['user'].id, "text": data["text"]}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
