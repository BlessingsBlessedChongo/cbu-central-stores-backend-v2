import time
import logging
from django.db import transaction
from .models import BlockchainLog
from .web3_client import web3_client

logger = logging.getLogger(__name__)

class EventListener:
    def __init__(self):
        self.last_block_processed = 0
        self.running = False
    
    def get_last_processed_block(self):
        """Get the highest block number from existing logs"""
        last_log = BlockchainLog.objects.order_by('-block_number').first()
        if last_log:
            return last_log.block_number
        return 0
    
    def process_events(self, from_block=None, to_block='latest'):
        """Process events from blockchain and save to database"""
        if not web3_client.contract:
            logger.warning("Contract not loaded, skipping event processing")
            return
        
        if from_block is None:
            from_block = self.get_last_processed_block() + 1
        
        try:
            all_events = web3_client.get_all_events(from_block=from_block, to_block=to_block)
            
            with transaction.atomic():
                events_processed = 0
                for event_name, events in all_events.items():
                    for event in events:
                        if self.save_event_log(event_name, event):
                            events_processed += 1
                
                logger.info(f"Processed {events_processed} events from block {from_block} to {to_block}")
                
                # Update last processed block if we processed any events
                if events_processed > 0:
                    self.last_block_processed = to_block if to_block != 'latest' else web3_client.get_latest_block()
        
        except Exception as e:
            logger.error(f"Error processing events: {e}")
    
    def save_event_log(self, event_name, event):
        """Save a single event log to database"""
        try:
            # Check if event already exists
            if BlockchainLog.objects.filter(
                transaction_hash=event['transactionHash'].hex(),
                log_index=event['logIndex']
            ).exists():
                return False
            
            # Create new log entry
            BlockchainLog.objects.create(
                event_type=event_name,
                transaction_hash=event['transactionHash'].hex(),
                block_number=event['blockNumber'],
                log_index=event['logIndex'],
                event_data=dict(event['args'])
            )
            return True
        
        except Exception as e:
            logger.error(f"Error saving event log {event_name}: {e}")
            return False
    
    def start_listening(self, interval=15):
        """Start continuous event listening"""
        self.running = True
        logger.info("Starting event listener...")
        
        try:
            while self.running:
                latest_block = web3_client.get_latest_block()
                if latest_block is not None and latest_block > self.last_block_processed:
                    self.process_events(from_block=self.last_block_processed + 1, to_block=latest_block)
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("Event listener stopped by user")
        except Exception as e:
            logger.error(f"Event listener crashed: {e}")
        finally:
            self.running = False
    
    def stop_listening(self):
        """Stop event listening"""
        self.running = False
        logger.info("Stopping event listener...")

# Global event listener instance
event_listener = EventListener()