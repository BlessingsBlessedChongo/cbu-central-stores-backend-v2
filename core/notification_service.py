import json
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from core.serializers import NotificationSerializer
from .models import CustomUser, Notification, NotificationPreference

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def create_notification(user, notification_type, title, message, priority='MEDIUM', 
                          related_object_type=None, related_object_id=None, action_url=None):
        """Create a new notification for a user"""
        try:
            # Check user notification preferences
            pref, created = NotificationPreference.objects.get_or_create(user=user)
            
            # Check if this type of notification is enabled
            if not NotificationService._is_notification_enabled(pref, notification_type):
                return None
            
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                action_url=action_url
            )
            
            # Send real-time notification via WebSocket
            NotificationService._send_websocket_notification(user, notification)
            
            # TODO: Add email and push notifications in production
            # if pref.email_enabled:
            #     NotificationService._send_email_notification(user, notification)
            # 
            # if pref.push_enabled:
            #     NotificationService._send_push_notification(user, notification)
            
            return notification
        
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    @staticmethod
    def _is_notification_enabled(preference, notification_type):
        """Check if the notification type is enabled in user preferences"""
        mapping = {
            'APPROVAL_PENDING': preference.approval_alerts,
            'APPROVAL_APPROVED': preference.approval_alerts,
            'APPROVAL_REJECTED': preference.approval_alerts,
            'STOCK_LOW': preference.low_stock_alerts,
            'DELIVERY_RECEIVED': preference.delivery_alerts,
            'DAMAGE_REPORTED': preference.damage_alerts,
            'RELOCATION_COMPLETED': preference.system_alerts,
            'SYSTEM_ALERT': preference.system_alerts,
            'REMINDER': preference.reminder_alerts,
        }
        
        return mapping.get(notification_type, True)
    
    @staticmethod
    def _send_websocket_notification(user, notification):
        """Send real-time notification via WebSocket"""
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}",
                    {
                        'type': 'send_notification',
                        'notification': NotificationSerializer(notification).data
                    }
                )
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")
    
    @staticmethod
    def create_approval_notification(request, stage, approver):
        """Create notification for approval actions"""
        if stage.approved:
            notification_type = 'APPROVAL_APPROVED'
            title = f"Request {request.id} Approved"
            message = f"Your request for {request.item_name} has been approved by {approver.username}"
        else:
            notification_type = 'APPROVAL_REJECTED'
            title = f"Request {request.id} Rejected"
            message = f"Your request for {request.item_name} has been rejected by {approver.username}"
        
        return NotificationService.create_notification(
            user=request.user,
            notification_type=notification_type,
            title=title,
            message=message,
            priority='HIGH',
            related_object_type='request',
            related_object_id=request.id,
            action_url=f"/requests/{request.id}"
        )
    
    @staticmethod
    def create_pending_approval_notification(request, stage):
        """Create notification for pending approvals"""
        # Find the appropriate approver based on stage
        role_mapping = {
            'STORES_MANAGER': 'stores_manager',
            'PROCUREMENT_OFFICER': 'procurement_officer',
            'CFO': 'cfo'
        }
        
        approver_role = role_mapping.get(stage.stage)
        if not approver_role:
            return None
        
        # Find users with the required role
        approvers = CustomUser.objects.filter(role=approver_role, is_active=True)
        
        notifications = []
        for approver in approvers:
            notification = NotificationService.create_notification(
                user=approver,
                notification_type='APPROVAL_PENDING',
                title=f"Approval Required - Request {request.id}",
                message=f"Request for {request.item_name} requires your approval",
                priority='HIGH',
                related_object_type='request',
                related_object_id=request.id,
                action_url=f"/approvals/pending"
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def create_low_stock_notification(stock):
        """Create low stock alert notification"""
        # Notify stores managers and admins
        recipients = CustomUser.objects.filter(
            role__in=['stores_manager', 'admin'],
            is_active=True
        )
        
        notifications = []
        for user in recipients:
            notification = NotificationService.create_notification(
                user=user,
                notification_type='STOCK_LOW',
                title=f"Low Stock Alert - {stock.item_name}",
                message=f"{stock.item_name} is running low. Current quantity: {stock.current_quantity}",
                priority='HIGH',
                related_object_type='stock',
                related_object_id=stock.id,
                action_url=f"/stocks/{stock.id}"
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def create_delivery_notification(delivery, recipient):
        """Create delivery notification"""
        return NotificationService.create_notification(
            user=recipient,
            notification_type='DELIVERY_RECEIVED',
            title=f"Delivery Received - {delivery.delivery_number}",
            message=f"Delivery for {delivery.stock.item_name} has been received",
            priority='MEDIUM',
            related_object_type='delivery',
            related_object_id=delivery.id,
            action_url=f"/deliveries/{delivery.id}"
        )
    
    @staticmethod
    def create_damage_report_notification(damage_report):
        """Create damage report notification"""
        # Notify stores managers and admins
        recipients = CustomUser.objects.filter(
            role__in=['stores_manager', 'admin'],
            is_active=True
        )
        
        notifications = []
        for user in recipients:
            notification = NotificationService.create_notification(
                user=user,
                notification_type='DAMAGE_REPORTED',
                title=f"Damage Reported - {damage_report.report_number}",
                message=f"Damage reported for {damage_report.stock.item_name}: {damage_report.description}",
                priority='HIGH',
                related_object_type='damage_report',
                related_object_id=damage_report.id,
                action_url=f"/damage-reports/{damage_report.id}"
            )
            if notification:
                notifications.append(notification)
        
        return notifications