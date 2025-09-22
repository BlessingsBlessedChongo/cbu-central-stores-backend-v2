from django.contrib import admin
from django.urls import path
from core.views import blockchain_status, process_events_now

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/blockchain/status/', blockchain_status, name='blockchain-status'),
    path('api/blockchain/process-events/', process_events_now, name='process-events'),
]
