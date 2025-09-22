import pytest
from unittest.mock import patch, MagicMock
from django.core.management import call_command
from core.models import BlockchainLog
from core.web3_client import web3_client

@pytest.mark.django_db
class TestEventListening:
    def test_blockchain_log_model(self):
        """Test BlockchainLog model creation"""
        log = BlockchainLog.objects.create(
            event_type='RequestCreated',
            transaction_hash='0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
            block_number=12345,
            log_index=0,
            event_data={'requestId': 1, 'department': '0x1234...'}
        )
        
        assert log.event_type == 'RequestCreated'
        assert str(log) == 'RequestCreated - 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
    
    @patch('core.web3_client.Web3Client.get_all_events')
    def test_event_processing(self, mock_get_events):
        """Test event processing with mock data"""
        # Mock blockchain events
        mock_events = {
            'RequestCreated': [
                {
                    'transactionHash': b'\x12\x34\x56\x78\x90\xab\xcd\xef\x12\x34\x56\x78\x90\xab\xcd\xef\x12\x34\x56\x78\x90\xab\xcd\xef\x12\x34\x56\x78\x90\xab\xcd\xef',
                    'blockNumber': 1001,
                    'logIndex': 0,
                    'args': {
                        'requestId': 1,
                        'department': '0x1234567890abcdef1234567890abcdef12345678',
                        'itemName': 'Laptops',
                        'quantity': 5,
                        'timestamp': 1234567890
                    }
                }
            ]
        }
        mock_get_events.return_value = mock_events
        
        # Process events
        from core.event_listener import event_listener
        event_listener.process_events(from_block=1000, to_block=1001)
        
        # Verify event was saved
        assert BlockchainLog.objects.count() == 1
        log = BlockchainLog.objects.first()
        assert log.event_type == 'RequestCreated'
        assert log.block_number == 1001
    
    def test_event_listener_command(self):
        """Test the management command"""
        # Should not crash when called
        try:
            call_command('start_event_listener', '--once')
            success = True
        except:
            success = False
        
        assert success, "Event listener command should run without crashing"