import json

from channels.generic.websocket import AsyncWebsocketConsumer


class MonitoringConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket untuk broadcast update monitoring live per ujian.

    Catatan:
    - Routing dan publish event dapat diaktifkan saat integrasi Channels
      di environment production.
    """

    async def connect(self):
        self.exam_id = self.scope["url_route"]["kwargs"]["exam_id"]
        self.group_name = f"monitoring_exam_{self.exam_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Endpoint ini bersifat one-way update. Pesan dari client diabaikan.
        return

    async def monitoring_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "monitoring.update",
                    "payload": event.get("payload", {}),
                }
            )
        )
