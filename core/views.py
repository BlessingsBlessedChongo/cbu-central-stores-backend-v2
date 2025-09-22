from rest_framework.decorators import api_view
from rest_framework.response import Response
from .web3_client import web3_client
from .event_listener import event_listener
from .models import BlockchainLog

@api_view(['GET'])
def blockchain_status(request):
    """Get blockchain connection status"""
    status = {
        'connected': web3_client.is_connected(),
        'contract_loaded': web3_client.contract is not None,
        'contract_address': web3_client.contract_address,
        'contract_info': web3_client.get_contract_info(),
        'latest_block': web3_client.get_latest_block(),
        'total_events_logged': BlockchainLog.objects.count()
    }
    return Response(status)

@api_view(['POST'])
def process_events_now(request):
    """Process events immediately"""
    try:
        event_listener.process_events()
        return Response({'status': 'success', 'message': 'Events processed'})
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=500)