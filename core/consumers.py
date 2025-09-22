import json
from time import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_authenticated:
            self.room_group_name = f"user_{self.user.id}"
            
            # Join user group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Leave user group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'mark_as_read':
                notification_id = text_data_json.get('notification_id')
                await self.mark_notification_as_read(notification_id)
                
        except json.JSONDecodeError:
            pass
    
    async def send_notification(self, event):
        """Send notification to WebSocket"""
        notification = event['notification']
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification
        }))
    
    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Mark notification as read"""
        from .models import Notification
        try:
            notification = Notification.objects.get(id=notification_id, user=self.user)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False