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


#stock management
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Stock(models.Model):
    item_name = models.CharField(max_length=200)
    original_quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    current_quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    cost_each = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    location = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='stocks')
    available = models.BooleanField(default=True)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['item_name']
        indexes = [
            models.Index(fields=['item_name']),
            models.Index(fields=['location']),
            models.Index(fields=['category']),
            models.Index(fields=['available']),
            models.Index(fields=['current_quantity']),
        ]
    
    def save(self, *args, **kwargs):
        # Update available status based on current quantity
        self.available = self.current_quantity > 0
        super().save(*args, **kwargs)
    
    @property
    def is_low_stock(self):
        return self.current_quantity <= self.low_stock_threshold
    
    @property
    def total_value(self):
        return self.current_quantity * self.cost_each
    
    def __str__(self):
        return f"{self.item_name} - {self.current_quantity} in {self.location}"

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
        ('TRANSFER', 'Transfer'),
    ]
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=15, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Positive for IN, negative for OUT
    previous_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()
    reason = models.TextField()
    reference = models.CharField(max_length=100, blank=True, null=True)  # PO number, request ID, etc.
    performed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['movement_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.stock.item_name} - {self.quantity}"


#Models for Delivery, Damage Report, Relocation 
class Delivery(models.Model):
    DELIVERY_STATUS = [
        ('PENDING', 'Pending'),
        ('RECEIVED', 'Received'),
        ('PARTIAL', 'Partially Received'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    
    delivery_number = models.CharField(max_length=20, unique=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='deliveries')
    supplier = models.CharField(max_length=200)
    ordered_quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    delivered_quantity = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    expected_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=DELIVERY_STATUS, default='PENDING')
    notes = models.TextField(blank=True, null=True)
    received_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_deliveries')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_deliveries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expected_date']
        indexes = [
            models.Index(fields=['delivery_number']),
            models.Index(fields=['status']),
            models.Index(fields=['expected_date']),
            models.Index(fields=['supplier']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.delivery_number:
            # Generate delivery number: DEL-001, DEL-002, etc.
            last_delivery = Delivery.objects.order_by('-created_at').first()
            if last_delivery and last_delivery.delivery_number.startswith('DEL-'):
                try:
                    last_num = int(last_delivery.delivery_number.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.delivery_number = f"DEL-{new_num:03d}"
        
        # Calculate total cost
        self.total_cost = self.ordered_quantity * self.unit_cost
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.delivery_number} - {self.stock.item_name} - {self.status}"

class DamageReport(models.Model):
    DAMAGE_SEVERITY = [
        ('MINOR', 'Minor Damage'),
        ('MODERATE', 'Moderate Damage'),
        ('SEVERE', 'Severe Damage'),
        ('TOTAL', 'Total Loss'),
    ]
    
    report_number = models.CharField(max_length=20, unique=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='damage_reports')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    severity = models.CharField(max_length=10, choices=DAMAGE_SEVERITY, default='MODERATE')
    description = models.TextField()
    location = models.CharField(max_length=100)
    reported_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='reported_damages')
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_damages')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_number']),
            models.Index(fields=['severity']),
            models.Index(fields=['resolved']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.report_number:
            # Generate report number: DAM-001, DAM-002, etc.
            last_report = DamageReport.objects.order_by('-created_at').first()
            if last_report and last_report.report_number.startswith('DAM-'):
                try:
                    last_num = int(last_report.report_number.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.report_number = f"DAM-{new_num:03d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.report_number} - {self.stock.item_name} - {self.get_severity_display()}"

class Relocation(models.Model):
    relocation_number = models.CharField(max_length=20, unique=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='relocations')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    from_location = models.CharField(max_length=100)
    to_location = models.CharField(max_length=100)
    reason = models.TextField()
    relocated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='relocations')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['relocation_number']),
            models.Index(fields=['from_location']),
            models.Index(fields=['to_location']),
            models.Index(fields=['completed']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.relocation_number:
            # Generate relocation number: REL-001, REL-002, etc.
            last_relocation = Relocation.objects.order_by('-created_at').first()
            if last_relocation and last_relocation.relocation_number.startswith('REL-'):
                try:
                    last_num = int(last_relocation.relocation_number.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.relocation_number = f"REL-{new_num:03d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.relocation_number} - {self.stock.item_name} - {self.from_location} to {self.to_location}"

#Models for Notifications and Reminders
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('APPROVAL_PENDING', 'Approval Pending'),
        ('APPROVAL_APPROVED', 'Approval Approved'),
        ('APPROVAL_REJECTED', 'Approval Rejected'),
        ('STOCK_LOW', 'Low Stock Alert'),
        ('DELIVERY_RECEIVED', 'Delivery Received'),
        ('DAMAGE_REPORTED', 'Damage Reported'),
        ('RELOCATION_COMPLETED', 'Relocation Completed'),
        ('SYSTEM_ALERT', 'System Alert'),
        ('REMINDER', 'Reminder'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    related_object_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'request', 'stock'
    related_object_id = models.CharField(max_length=50, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    action_url = models.CharField(max_length=500, blank=True, null=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)  # For scheduled notifications
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['scheduled_for']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} - {self.title}"

class NotificationPreference(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='notification_preferences')
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    websocket_enabled = models.BooleanField(default=True)
    low_stock_alerts = models.BooleanField(default=True)
    approval_alerts = models.BooleanField(default=True)
    delivery_alerts = models.BooleanField(default=True)
    damage_alerts = models.BooleanField(default=True)
    reminder_alerts = models.BooleanField(default=True)
    system_alerts = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Notification Preferences"