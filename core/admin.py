from django.contrib import admin
from .models import ApprovalHistory, BlockchainLog, CustomUser, DepartmentRequest

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