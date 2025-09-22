from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="CBU Central Stores API",
        default_version='v2',
        description="Blockchain-based Central Stores Management System",
        terms_of_service="https://cbu.edu.zm/terms/",
        contact=openapi.Contact(email="stores@cbu.edu.zm"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    # API Documentation
    path('', views.api_overview, name='api-overview'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

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

    # Delivery endpoints
    path('api/deliveries/', views.create_delivery, name='create-delivery'),  # POST
    path('api/deliveries/', views.get_all_deliveries, name='all-deliveries'),  # GET
    path('api/deliveries/<int:delivery_id>/', views.get_delivery_by_id, name='get-delivery'),
    path('api/deliveries/<int:delivery_id>/', views.update_delivery, name='update-delivery'),  # PUT
    
    # Damage report endpoints
    path('api/report-damage/', views.report_damage, name='report-damage'),  # POST
    path('api/damage-reports/', views.get_all_damage_reports, name='all-damage-reports'),  # GET
    path('api/damage-reports/<int:report_id>/', views.update_damage_report, name='update-damage-report'),  # PUT
    
    # Relocation endpoints
    path('api/relocate/', views.relocate_stock, name='relocate-stock'),  # POST
    path('api/relocations/', views.get_all_relocations, name='all-relocations'),  # GET

    # Notification endpoints
    path('api/notifications/', views.get_user_notifications, name='user-notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_as_read, name='mark-notification-read'),
    path('api/notifications/read-all/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    path('api/notification-preferences/', views.notification_preferences, name='notification-preferences'),
    path('api/test-notification/', views.send_test_notification, name='test-notification'),
]