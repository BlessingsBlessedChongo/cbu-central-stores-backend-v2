from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints (exact match frontend requirements)
    path('api/auth/register/', views.register_user, name='register'),
    path('api/auth/login/', views.login_user, name='login'),
    path('api/auth/logout/', views.logout_user, name='logout'),
    path('api/auth/me/', views.get_current_user, name='current-user'),
    path('api/auth/users/', views.get_all_users, name='all-users'),
    path('api/auth/users/<int:user_id>/', views.update_user, name='update-user'),
    path('api/auth/users/delete/<int:user_id>/', views.delete_user, name='delete-user'),
    
    # Blockchain endpoints
    path('api/blockchain/status/', views.blockchain_status, name='blockchain-status'),
    path('api/blockchain/process-events/', views.process_events_now, name='process-events'),
]