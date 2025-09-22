from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator

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

class DepartmentRequest(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
    ]
    
    id = models.CharField(max_length=20, primary_key=True, unique=True)  # req-001 format
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='requests'
    )
    item_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    department = models.CharField(max_length=50, choices=CustomUser.DEPARTMENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['department']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generate ID in format: req-001, req-002, etc.
            last_request = DepartmentRequest.objects.order_by('-created_at').first()
            if last_request and last_request.id.startswith('req-'):
                try:
                    last_num = int(last_request.id.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.id = f"req-{new_num:03d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.id} - {self.item_name} ({self.status})"

class ApprovalHistory(models.Model):
    request = models.ForeignKey(
        DepartmentRequest, 
        on_delete=models.CASCADE, 
        related_name='approval_history'
    )
    approver = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='approvals'
    )
    approved = models.BooleanField()
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Approval Histories'
    
    def __str__(self):
        status = "Approved" if self.approved else "Rejected"
        return f"{self.request.id} - {self.approver.username} - {status}"

class ApprovalStage(models.Model):
    STAGE_CHOICES = [
        ('STORES_MANAGER', 'Stores Manager Approval'),
        ('PROCUREMENT_OFFICER', 'Procurement Officer Approval'),
        ('CFO', 'Chief Financial Officer Approval'),
        ('COMPLETED', 'Approval Completed'),
    ]
    
    request = models.ForeignKey(
        DepartmentRequest, 
        on_delete=models.CASCADE, 
        related_name='approval_stages'
    )
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    required = models.BooleanField(default=True)
    completed = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    approver = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stage_approvals'
    )
    comments = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['completed']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.request.id} - {self.get_stage_display()} - {'Completed' if self.completed else 'Pending'}"

class ApprovalFlow(models.Model):
    name = models.CharField(max_length=100, default='Default Approval Flow')
    stages = models.JSONField(default=list)  # List of stage configurations
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

# Add method to DepartmentRequest model
def initialize_approval_stages(self):
    """Initialize approval stages for a new request"""
    # Default approval flow: Stores → Procurement → CFO
    stages = [
        ('STORES_MANAGER', 'Stores Manager Approval', True),
        ('PROCUREMENT_OFFICER', 'Procurement Officer Approval', True),
        ('CFO', 'Chief Financial Officer Approval', True),
    ]
    
    for stage_type, _, required in stages:
        ApprovalStage.objects.create(
            request=self,
            stage=stage_type,
            required=required,
            completed=False,
            approved=False
        )

# Add the method to DepartmentRequest model
DepartmentRequest.initialize_approval_stages = initialize_approval_stages

# Add property to check current status
@property
def current_approval_stage(self):
    """Get the current pending approval stage"""
    return self.approval_stages.filter(completed=False).order_by('created_at').first()

DepartmentRequest.current_approval_stage = current_approval_stage

# Add property to check if fully approved
@property
def is_fully_approved(self):
    """Check if all required approval stages are completed and approved"""
    required_stages = self.approval_stages.filter(required=True)
    if not required_stages.exists():
        return False
    return all(stage.completed and stage.approved for stage in required_stages)

DepartmentRequest.is_fully_approved = is_fully_approved