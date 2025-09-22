import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from .models import ApprovalStage, CustomUser, Stock, Notification
from .notification_service import NotificationService
from django.db import models

logger = logging.getLogger(__name__)

@shared_task
def send_approval_reminders():
    """Send reminders for pending approvals"""
    try:
        # Find pending approval stages that are overdue or due soon
        pending_stages = ApprovalStage.objects.filter(
            completed=False,
            required=True
        ).select_related('request', 'request__user')
        
        for stage in pending_stages:
            # Check if reminder is needed (e.g., stage is overdue)
            if stage.due_date and stage.due_date <= timezone.now():
                # Send reminder to approver
                role_mapping = {
                    'STORES_MANAGER': 'stores_manager',
                    'PROCUREMENT_OFFICER': 'procurement_officer',
                    'CFO': 'cfo'
                }
                
                approver_role = role_mapping.get(stage.stage)
                if approver_role:
                    approvers = CustomUser.objects.filter(role=approver_role, is_active=True)
                    
                    for approver in approvers:
                        NotificationService.create_notification(
                            user=approver,
                            notification_type='REMINDER',
                            title=f"Reminder: Approval Required - Request {stage.request.id}",
                            message=f"Request for {stage.request.item_name} is awaiting your approval. Please review it soon.",
                            priority='MEDIUM',
                            related_object_type='request',
                            related_object_id=stage.request.id,
                            action_url=f"/approvals/pending"
                        )
        
        logger.info(f"Sent approval reminders for {pending_stages.count()} pending stages")
        
    except Exception as e:
        logger.error(f"Error sending approval reminders: {e}")

@shared_task
def check_low_stock():
    """Check for low stock items and send alerts"""
    try:
        low_stock_items = Stock.objects.filter(
            current_quantity__lte=models.F('low_stock_threshold'),
            available=True
        )
        
        for stock in low_stock_items:
            NotificationService.create_low_stock_notification(stock)
        
        logger.info(f"Checked low stock for {low_stock_items.count()} items")
        
    except Exception as e:
        logger.error(f"Error checking low stock: {e}")

@shared_task
def cleanup_old_notifications():
    """Clean up old read notifications"""
    try:
        # Delete read notifications older than 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        deleted_count, _ = Notification.objects.filter(
            is_read=True,
            created_at__lte=thirty_days_ago
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {e}")