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

    # Requests endpoints (exact match to API documentation)
    path('api/requests/', views.get_all_requests, name='all-requests'), # GET
    path('api/requests/', views.create_request, name='create-request'),  # POST
    path('api/requests/<str:request_id>/', views.get_request_by_id, name='get-request'),# GET
    path('api/requests/<str:request_id>/', views.update_request, name='update-request'),  # PUT
    path('api/requests/<str:request_id>/', views.delete_request, name='delete-request'),  # DELETE
    
    # Blockchain endpoints
    path('api/blockchain/status/', views.blockchain_status, name='blockchain-status'),
    path('api/blockchain/process-events/', views.process_events_now, name='process-events'),

    # Approval workflow endpoints
    path('api/requests/<str:request_id>/details/', views.get_request_with_approvals, name='request-details'),
    path('api/requests/<str:request_id>/approve/<int:stage_id>/', views.approve_request, name='approve-request'),
    path('api/approvals/pending/', views.get_pending_approvals, name='pending-approvals'),
    path('api/requests/<str:request_id>/history/', views.get_approval_history, name='approval-history'),

    # Stock management endpoints (exact match to API documentation)
    path('api/stocks/', views.get_all_stocks, name='all-stocks'),
    path('api/stocks/', views.create_stock_item, name='create-stock'),  # POST
    path('api/stocks/<int:stock_id>/', views.get_stock_by_id, name='get-stock'),
    path('api/stocks/<int:stock_id>/', views.update_stock_item, name='update-stock'),  # PUT
    path('api/stocks/<int:stock_id>/', views.delete_stock_item, name='delete-stock'),  # DELETE
    
    # Additional stock endpoints
    path('api/stocks/<int:stock_id>/movements/', views.get_stock_movements, name='stock-movements'),
    path('api/stocks/alerts/low-stock/', views.get_low_stock_alerts, name='low-stock-alerts'),
    path('api/stocks/categories/', views.get_categories, name='categories'),
]