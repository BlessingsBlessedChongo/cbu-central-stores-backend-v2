from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import ApprovalHistory, ApprovalStage, Category, CustomUser, DamageReport, Delivery, DepartmentRequest, Relocation, Stock, StockMovement

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    firstname = serializers.CharField(source='first_name', required=False)
    lastname = serializers.CharField(source='last_name', required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'password', 'firstname', 'lastname',
            'role', 'department', 'blockchain_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        
        user = CustomUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                    return data
                raise serializers.ValidationError('User account is disabled.')
            raise serializers.ValidationError('Invalid credentials.')
        raise serializers.ValidationError('Must include username and password.')

class UserSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'firstname', 'lastname',
            'role', 'department', 'blockchain_address', 'created_at', 'updated_at'
        ]

class UserUpdateSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name', required=False)
    lastname = serializers.CharField(source='last_name', required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'firstname', 'lastname',
            'role', 'department', 'blockchain_address'
        ]

class RequestSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source='user.username', read_only=True)
    item = serializers.CharField(source='item_name')
    createdAt = serializers.DateTimeField(source='created_at', format='%Y-%m-%dT%H:%M:%SZ')
    updatedAt = serializers.DateTimeField(source='updated_at', format='%Y-%m-%dT%H:%M:%SZ')
    
    class Meta:
        model = DepartmentRequest
        fields = [
            'id', 'user_id', 'item', 'quantity', 'priority', 
            'reason', 'status', 'department', 'createdAt', 'updatedAt'
        ]
        read_only_fields = ['id', 'user_id', 'createdAt', 'updatedAt']

class RequestCreateSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item')
    requester_id = serializers.CharField(write_only=True)
    
    class Meta:
        model = DepartmentRequest
        fields = [
            'item_name', 'quantity', 'priority', 'reason', 
            'status', 'requester_id', 'department'
        ]
    
    def validate_requester_id(self, value):
        try:
            user = CustomUser.objects.get(username=value)
            return user
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('User not found')
    
    def create(self, validated_data):
        user = validated_data.pop('requester_id')
        validated_data['user'] = user
        return super().create(validated_data)

class RequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentRequest
        fields = ['status', 'priority']
        extra_kwargs = {
            'status': {'required': False},
            'priority': {'required': False},
        }

class ApprovalStageSerializer(serializers.ModelSerializer):
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    approver_name = serializers.CharField(source='approver.username', read_only=True, allow_null=True)
    
    class Meta:
        model = ApprovalStage
        fields = [
            'id', 'stage', 'stage_display', 'required', 'completed', 
            'approved', 'approver', 'approver_name', 'comments',
            'due_date', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']

class ApprovalHistorySerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.username', read_only=True)
    approver_role = serializers.CharField(source='approver.get_role_display', read_only=True)
    
    class Meta:
        model = ApprovalHistory
        fields = [
            'id', 'approver', 'approver_name', 'approver_role',
            'approved', 'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class RequestDetailSerializer(RequestSerializer):
    """Extended serializer with approval information"""
    approval_stages = ApprovalStageSerializer(many=True, read_only=True)
    approval_history = ApprovalHistorySerializer(many=True, read_only=True)
    current_stage = serializers.SerializerMethodField()
    is_fully_approved = serializers.BooleanField(read_only=True)
    
    class Meta(RequestSerializer.Meta):
        fields = RequestSerializer.Meta.fields + [
            'approval_stages', 'approval_history', 
            'current_stage', 'is_fully_approved'
        ]
    
    def get_current_stage(self, obj):
        current = obj.current_approval_stage
        if current:
            return {
                'stage': current.stage,
                'stage_display': current.get_stage_display(),
                'due_date': current.due_date
            }
        return None

class ApprovalActionSerializer(serializers.Serializer):
    approved = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=True, max_length=500)
    comments = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class StockSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', allow_null=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    
    class Meta:
        model = Stock
        fields = [
            'id', 'item_name', 'original_quantity', 'current_quantity',
            'cost_each', 'location', 'available', 'category',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'available', 'created_at', 'updated_at']

class StockCreateSerializer(serializers.ModelSerializer):
    category = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Stock
        fields = [
            'item_name', 'original_quantity', 'current_quantity',
            'cost_each', 'location', 'category'
        ]
    
    def create(self, validated_data):
        category_name = validated_data.pop('category', None)
        if category_name:
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'description': f'Auto-created category for {category_name}'}
            )
            validated_data['category'] = category
        return super().create(validated_data)

class StockUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['current_quantity', 'location']
        extra_kwargs = {
            'current_quantity': {'required': False},
            'location': {'required': False},
        }

class StockMovementSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source='performed_by.username', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    item_name = serializers.CharField(source='stock.item_name', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'stock', 'item_name', 'movement_type', 'movement_type_display',
            'quantity', 'previous_quantity', 'new_quantity', 'reason',
            'reference', 'performed_by', 'performed_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DeliverySerializer(serializers.ModelSerializer):
    stock_name = serializers.CharField(source='stock.item_name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    
    class Meta:
        model = Delivery
        fields = [
            'id', 'delivery_number', 'stock', 'stock_name', 'supplier',
            'ordered_quantity', 'delivered_quantity', 'unit_cost', 'total_cost',
            'expected_date', 'actual_date', 'status', 'notes',
            'received_by', 'received_by_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'delivery_number', 'total_cost', 'created_at', 'updated_at']

class DeliveryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            'stock', 'supplier', 'ordered_quantity', 'unit_cost',
            'expected_date', 'notes'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class DeliveryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['delivered_quantity', 'actual_date', 'status', 'notes', 'received_by']

class DamageReportSerializer(serializers.ModelSerializer):
    stock_name = serializers.CharField(source='stock.item_name', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    resolved_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ', allow_null=True)
    
    class Meta:
        model = DamageReport
        fields = [
            'id', 'report_number', 'stock', 'stock_name', 'quantity',
            'severity', 'description', 'location', 'reported_by', 'reported_by_name',
            'resolved', 'resolution_notes', 'resolved_by', 'resolved_by_name',
            'resolved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'report_number', 'created_at', 'updated_at']

class DamageReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamageReport
        fields = ['stock', 'quantity', 'severity', 'description', 'location']
    
    def create(self, validated_data):
        validated_data['reported_by'] = self.context['request'].user
        return super().create(validated_data)

class DamageReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamageReport
        fields = ['resolved', 'resolution_notes', 'resolved_by']

class RelocationSerializer(serializers.ModelSerializer):
    stock_name = serializers.CharField(source='stock.item_name', read_only=True)
    relocated_by_name = serializers.CharField(source='relocated_by.username', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    completed_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ', allow_null=True)
    
    class Meta:
        model = Relocation
        fields = [
            'id', 'relocation_number', 'stock', 'stock_name', 'quantity',
            'from_location', 'to_location', 'reason', 'relocated_by', 'relocated_by_name',
            'completed', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'relocation_number', 'created_at', 'updated_at']

class RelocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relocation
        fields = ['stock', 'quantity', 'from_location', 'to_location', 'reason']
    
    def create(self, validated_data):
        validated_data['relocated_by'] = self.context['request'].user
        return super().create(validated_data)

class RelocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relocation
        fields = ['completed', 'completed_at']