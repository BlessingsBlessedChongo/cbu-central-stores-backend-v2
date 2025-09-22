from pyexpat.errors import messages
from django.contrib import admin
from .models import ApprovalHistory, BlockchainLog, Category, CustomUser, DamageReport, Delivery, DepartmentRequest, Relocation, Stock, StockMovement

@admin.register(BlockchainLog)
class BlockchainLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'transaction_hash_short', 'block_number', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['transaction_hash', 'event_data']
    readonly_fields = ['event_type', 'transaction_hash', 'block_number', 'log_index', 'event_data', 'timestamp']
    
    def transaction_hash_short(self, obj):
        return f"{obj.transaction_hash[:10]}...{obj.transaction_hash[-8:]}"
    transaction_hash_short.short_description = 'Transaction Hash'

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'department', 'blockchain_address_short']
    list_filter = ['role', 'department']
    search_fields = ['username', 'email', 'blockchain_address']
    
    def blockchain_address_short(self, obj):
        if obj.blockchain_address:
            return f"{obj.blockchain_address[:8]}...{obj.blockchain_address[-6:]}"
        return "Not set"
    blockchain_address_short.short_description = 'Blockchain Address'

    actions = ['generate_blockchain_credentials', 'reset_passwords']
    
    def generate_blockchain_credentials(self, request, queryset):
        """Admin action to generate blockchain credentials for users"""
        from web3 import Web3
        
        for user in queryset:
            if not user.has_blockchain_credentials():
                # Generate new account
                account = Web3().eth.account.create()
                user.set_blockchain_credentials(
                    account.address,
                    account.key.hex()
                )
                self.message_user(
                    request,
                    f"Generated blockchain credentials for {user.username}",
                    messages.SUCCESS
                )
    
    generate_blockchain_credentials.short_description = "Generate blockchain credentials for selected users"
    
    def reset_passwords(self, request, queryset):
        """Admin action to reset user passwords"""
        for user in queryset:
            new_password = CustomUser.objects.make_random_password(length=16)
            user.set_password(new_password)
            user.save()
            self.message_user(
                request,
                f"Password reset for {user.username}: {new_password}",
                messages.WARNING
            )
    
    reset_passwords.short_description = "Reset passwords for selected users"

@admin.register(DepartmentRequest)
class DepartmentRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'item_name', 'user', 'quantity', 'priority', 'status', 'department', 'created_at']
    list_filter = ['status', 'priority', 'department', 'created_at']
    search_fields = ['id', 'item_name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(ApprovalHistory)
class ApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = ['request', 'approver', 'approved', 'created_at']
    list_filter = ['approved', 'created_at']
    search_fields = ['request__id', 'approver__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'current_quantity', 'location', 'category', 'available', 'is_low_stock', 'created_at']
    list_filter = ['category', 'location', 'available', 'created_at']
    search_fields = ['item_name', 'location']
    readonly_fields = ['created_at', 'updated_at', 'available', 'is_low_stock']
    ordering = ['item_name']
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['stock', 'movement_type', 'quantity', 'previous_quantity', 'new_quantity', 'performed_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['stock__item_name', 'reason', 'reference']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['delivery_number', 'stock', 'supplier', 'ordered_quantity', 'delivered_quantity', 'status', 'expected_date', 'created_at']
    list_filter = ['status', 'expected_date', 'created_at']
    search_fields = ['delivery_number', 'stock__item_name', 'supplier']
    readonly_fields = ['delivery_number', 'total_cost', 'created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(DamageReport)
class DamageReportAdmin(admin.ModelAdmin):
    list_display = ['report_number', 'stock', 'quantity', 'severity', 'resolved', 'reported_by', 'created_at']
    list_filter = ['severity', 'resolved', 'created_at']
    search_fields = ['report_number', 'stock__item_name', 'description']
    readonly_fields = ['report_number', 'created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(Relocation)
class RelocationAdmin(admin.ModelAdmin):
    list_display = ['relocation_number', 'stock', 'quantity', 'from_location', 'to_location', 'completed', 'relocated_by', 'created_at']
    list_filter = ['completed', 'created_at']
    search_fields = ['relocation_number', 'stock__item_name', 'from_location', 'to_location']
    readonly_fields = ['relocation_number', 'created_at', 'updated_at']
    ordering = ['-created_at']