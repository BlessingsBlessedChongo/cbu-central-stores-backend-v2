from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class BlockchainLog(models.Model):
    EVENT_TYPES = [
        ('RoleAssigned', 'Role Assigned'),
        ('RequestCreated', 'Request Created'),
        ('RequestApproved', 'Request Approved'),
        ('StockAdjusted', 'Stock Adjusted'),
        ('DeliveryLogged', 'Delivery Logged'),
        ('DamageReported', 'Damage Reported'),
        ('RelocationLogged', 'Relocation Logged'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    transaction_hash = models.CharField(max_length=66)  # 0x + 64 chars
    block_number = models.PositiveBigIntegerField()

    log_index = models.PositiveIntegerField()
    event_data = models.JSONField()  # Store all event parameters
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['transaction_hash', 'log_index']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['block_number']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.transaction_hash}"

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('stores_manager', 'Stores Manager'),
        ('procurement_officer', 'Procurement Officer'),
        ('cfo', 'Chief Financial Officer'),
        ('department_dean', 'Department Dean'),
    ]

    DEPARTMENT_CHOICES = [
        ('IT_ADMIN', 'IT Administration'),
        ('PROCUREMENT', 'Procurement'),
        ('FINANCE', 'Finance'),
        ('COMPUTER_SCIENCE', 'Computer Science'),
        ('ENGINEERING', 'Engineering'),
        ('BUSINESS', 'Business Studies'),
        ('MEDICINE', 'Medicine'),
        ('EDUCATION', 'Education'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='department_dean')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True, null=True)
    blockchain_address = models.CharField(max_length=42, blank=True, null=True)
    encrypted_private_key = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Add unique related_name to resolve conflicts with built-in User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="customuser_set",  # Changed from default 'user_set'
        related_query_name="customuser",
    )
    class Meta:
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['department']),
            models.Index(fields=['username']),
        ]
    
    
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set",  # Changed from default 'user_set'
        related_query_name="customuser",
    )
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"