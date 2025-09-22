import time
import logging
from django.core.management.base import BaseCommand
from core.event_listener import event_listener

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start listening for blockchain events and save them to database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=15,
            help='Polling interval in seconds (default: 15)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Process events once and exit'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        process_once = options['once']
        
        self.stdout.write(
            self.style.SUCCESS('Starting blockchain event listener...')
        )
        
        if process_once:
            self.stdout.write('Processing events once...')
            event_listener.process_events()
            self.stdout.write(
                self.style.SUCCESS('Event processing completed')
            )
        else:
            self.stdout.write(f'Starting continuous listening (interval: {interval}s)...')
            try:
                event_listener.start_listening(interval)
            except KeyboardInterrupt:
                self.stdout.write('\nEvent listener stopped by user')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Event listener crashed: {e}')
                )