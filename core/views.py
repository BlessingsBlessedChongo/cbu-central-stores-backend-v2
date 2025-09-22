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