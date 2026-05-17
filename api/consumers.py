from channels.generic.websocket import AsyncJsonWebsocketConsumer

class GroupConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'group_{self.group_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def receive_json(self, content, **kwargs):
        pass

    async def expense_update(self, event):
        await self.send_json(event['data'])