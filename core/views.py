from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from .models import CustomUser, BlockchainLog
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer,
    UserSerializer, UserUpdateSerializer
)
from .web3_client import web3_client
from .event_listener import event_listener

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """Register new user - Admin only"""
    if not request.user.is_authenticated or request.user.role != 'admin':
        return Response(
            {'error': 'Only administrators can register users'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # TODO: Assign blockchain role in next batch
        user_data = UserSerializer(user).data
        
        return Response(user_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    """User login"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        user_data = UserSerializer(user).data
        
        return Response({
            'user': user_data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    """User logout"""
    logout(request)
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_current_user(request):
    """Get current user info"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def get_all_users(request):
    """Get all users - Admin only"""
    users = CustomUser.objects.all().order_by('-created_at')
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([permissions.IsAdminUser])
def update_user(request, user_id):
    """Update user - Admin only"""
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAdminUser])
def delete_user(request, user_id):
    """Delete user - Admin only"""
    try:
        user = CustomUser.objects.get(id=user_id)
        user.delete()
        return Response(
            {'message': 'User deleted successfully'}, 
            status=status.HTTP_200_OK
        )
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# Blockchain views (from previous batch)
@api_view(['GET'])
def blockchain_status(request):
    """Get blockchain connection status"""
    status_data = {
        'connected': web3_client.is_connected(),
        'contract_loaded': web3_client.contract is not None,
        'contract_address': web3_client.contract_address,
        'contract_info': web3_client.get_contract_info(),
        'latest_block': web3_client.get_latest_block(),
        'total_events_logged': BlockchainLog.objects.count()
    }
    return Response(status_data)

@api_view(['POST'])
def process_events_now(request):
    """Process events immediately"""
    try:
        event_listener.process_events()
        return Response({'status': 'success', 'message': 'Events processed'})
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
from django.db.models import Q
from .models import DepartmentRequest, ApprovalHistory
from .serializers import (
    RequestSerializer, RequestCreateSerializer, RequestUpdateSerializer
)


# Request management views

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_request(request):
    """Create a new request - Exact match to API doc"""
    serializer = RequestCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Department Deans can only create requests for their department
        if request.user.role == 'department_dean':
            serializer.validated_data['department'] = request.user.department
        
        request_obj = serializer.save()
        
        # Initialize approval stages
        request_obj.initialize_approval_stages()
        
        # Blockchain logging
        try:
            if web3_client.contract:
                web3_client.contract.functions.createRequest(
                    request_obj.item_name,
                    request_obj.quantity,
                    request_obj.priority,
                    request_obj.reason
                ).transact({
                    'from': request.user.blockchain_address,
                    'gas': 100000
                })
        except Exception as e:
            # Log blockchain error but don't fail the request
            print(f"Blockchain error: {e}")
        
        response_serializer = RequestSerializer(request_obj)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_all_requests(request):
    """Get all requests with filtering - Exact match to API doc"""
    requests = DepartmentRequest.objects.all()
    
    # Apply filters based on query parameters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    
    if status_filter:
        requests = requests.filter(status=status_filter.upper())
    if priority_filter:
        requests = requests.filter(priority=priority_filter.upper())
    
    # Role-based filtering
    if request.user.role == 'department_dean':
        requests = requests.filter(department=request.user.department)
    
    serializer = RequestSerializer(requests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_request_by_id(request, request_id):
    """Get single request by ID - Exact match to API doc"""
    try:
        request_obj = DepartmentRequest.objects.get(id=request_id)
        
        # Department Deans can only see their own requests
        if (request.user.role == 'department_dean' and 
            request_obj.department != request.user.department):
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RequestSerializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except DepartmentRequest.DoesNotExist:
        return Response(
            {'error': 'Request not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_request(request, request_id):
    """Update request - Exact match to API doc"""
    try:
        request_obj = DepartmentRequest.objects.get(id=request_id)
        
        # Check permissions
        if request.user.role == 'department_dean' and request_obj.user != request.user:
            return Response(
                {'error': 'Can only update your own requests'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RequestUpdateSerializer(request_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            response_serializer = RequestSerializer(request_obj)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except DepartmentRequest.DoesNotExist:
        return Response(
            {'error': 'Request not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_request(request, request_id):
    """Delete request - Exact match to API doc"""
    try:
        request_obj = DepartmentRequest.objects.get(id=request_id)
        
        # Only request owner or admin can delete
        if request_obj.user != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'Cannot delete this request'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        request_obj.delete()
        return Response(
            {'message': 'Request deleted successfully'}, 
            status=status.HTTP_200_OK
        )
    
    except DepartmentRequest.DoesNotExist:
        return Response(
            {'error': 'Request not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    

from django.utils import timezone
from .models import ApprovalStage, ApprovalHistory, ApprovalFlow
from .serializers import (
    RequestDetailSerializer, ApprovalActionSerializer,
    ApprovalStageSerializer, ApprovalHistorySerializer
)
from .web3_client import web3_client

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_request_with_approvals(request, request_id):
    """Get request details with approval information"""
    try:
        request_obj = DepartmentRequest.objects.get(id=request_id)
        
        # Check permissions
        if (request.user.role == 'department_dean' and 
            request_obj.department != request.user.department):
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RequestDetailSerializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except DepartmentRequest.DoesNotExist:
        return Response(
            {'error': 'Request not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_request(request, request_id, stage_id):
    """Approve or reject a request at specific stage"""
    try:
        request_obj = DepartmentRequest.objects.get(id=request_id)
        approval_stage = ApprovalStage.objects.get(id=stage_id, request=request_obj)
        
        # Check if stage is already completed
        if approval_stage.completed:
            return Response(
                {'error': 'This approval stage is already completed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check user permissions based on stage
        if not can_approve_stage(request.user, approval_stage.stage):
            return Response(
                {'error': 'You are not authorized to approve this stage'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ApprovalActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        approved = serializer.validated_data['approved']
        reason = serializer.validated_data['reason']
        comments = serializer.validated_data.get('comments', '')
        
        # Update approval stage
        approval_stage.completed = True
        approval_stage.approved = approved
        approval_stage.approver = request.user
        approval_stage.comments = comments
        approval_stage.completed_at = timezone.now()
        approval_stage.save()
        
        # Create approval history
        ApprovalHistory.objects.create(
            request=request_obj,
            approver=request.user,
            approved=approved,
            reason=reason
        )
        
        # Update request status based on approval result
        if not approved:
            request_obj.status = 'REJECTED'
            request_obj.save()
        else:
            # Check if all stages are completed
            if request_obj.is_fully_approved:
                request_obj.status = 'APPROVED'
                request_obj.save()
            else:
                request_obj.status = 'PROCESSING'
                request_obj.save()
        
        # Blockchain logging
        try:
            if web3_client.contract:
                web3_client.contract.functions.approveRequest(
                    int(request_obj.id.split('-')[1]),  # Extract numeric ID
                    approved,
                    reason
                ).transact({
                    'from': request.user.blockchain_address,
                    'gas': 100000
                })
        except Exception as e:
            # Log blockchain error but don't fail the request
            print(f"Blockchain error: {e}")
        
        # Return updated request details
        serializer = RequestDetailSerializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except DepartmentRequest.DoesNotExist:
        return Response(
            {'error': 'Request not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except ApprovalStage.DoesNotExist:
        return Response(
            {'error': 'Approval stage not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_pending_approvals(request):
    """Get pending approvals for the current user"""
    user_role = request.user.role
    stage_mapping = {
        'stores_manager': 'STORES_MANAGER',
        'procurement_officer': 'PROCUREMENT_OFFICER',
        'cfo': 'CFO'
    }
    
    if user_role not in stage_mapping:
        return Response([], status=status.HTTP_200_OK)
    
    stage_type = stage_mapping[user_role]
    pending_approvals = ApprovalStage.objects.filter(
        stage=stage_type,
        completed=False,
        required=True
    ).select_related('request')
    
    # Filter requests that are in processing status
    results = []
    for approval in pending_approvals:
        if approval.request.status == 'PROCESSING':
            results.append({
                'request_id': approval.request.id,
                'item_name': approval.request.item_name,
                'quantity': approval.request.quantity,
                'department': approval.request.department,
                'priority': approval.request.priority,
                'stage_id': approval.id,
                'stage': approval.stage,
                'due_date': approval.due_date,
                'created_at': approval.request.created_at
            })
    
    return Response(results, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_approval_history(request, request_id):
    """Get approval history for a request"""
    try:
        request_obj = DepartmentRequest.objects.get(id=request_id)
        
        # Check permissions
        if (request.user.role == 'department_dean' and 
            request_obj.department != request.user.department):
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        history = ApprovalHistory.objects.filter(request=request_obj).order_by('created_at')
        serializer = ApprovalHistorySerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except DepartmentRequest.DoesNotExist:
        return Response(
            {'error': 'Request not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

# Helper function
def can_approve_stage(user, stage_type):
    """Check if user can approve a specific stage"""
    role_mapping = {
        'STORES_MANAGER': 'stores_manager',
        'PROCUREMENT_OFFICER': 'procurement_officer',
        'CFO': 'cfo'
    }
    
    if stage_type not in role_mapping:
        return False
    
    return user.role == role_mapping[stage_type]