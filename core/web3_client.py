import os
import json
import logging
from web3 import Web3
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Web3Client:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Web3Client, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Web3 connection and contract"""
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URI', 'http://127.0.0.1:7545')))
        
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.contract = None
        self.abi = None
        
        if self.contract_address and self.contract_address != 'None':
            self.load_contract()
    
    def load_contract(self):
        """Load the deployed contract"""
        if not self.contract_address or self.contract_address == 'None':
            logger.warning("Contract address not set in environment variables")
            return False
        
        try:
            # Load ABI
            build_dir = os.path.join(settings.BASE_DIR, 'contracts', 'build')
            compiled_path = os.path.join(build_dir, 'compiled_contract.json')
            
            with open(compiled_path, 'r') as file:
                compiled_sol = json.load(file)
            
            # Extract ABI from compiled contract
            self.abi = compiled_sol['contracts']['StreamlinedStoresManagerV3.sol']['StreamlinedStoresManagerV3']['abi']
            
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.abi
            )
            logger.info(f"Contract loaded successfully at address: {self.contract_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to load contract: {e}")
            return False
    
    def is_connected(self):
        """Check if connected to blockchain"""
        return self.w3.is_connected()
    
    def get_contract_info(self):
        """Get contract information"""
        if not self.contract:
            if not self.load_contract():
                return "Contract not available"
        
        try:
            return self.contract.functions.getContractInfo().call()
        except Exception as e:
            return f"Error getting contract info: {e}"
    
    def get_latest_block(self):
        """Get the latest block number"""
        try:
            return self.w3.eth.block_number
        except Exception as e:
            logger.error(f"Error getting latest block: {e}")
            return None
    
    def get_account_balance(self, address):
        """Get balance of an account in ETH"""
        try:
            balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            return self.w3.from_wei(balance_wei, 'ether')
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            return None
    
    def get_events(self, event_name, from_block=0, to_block='latest'):
        """Get events from the contract"""
        if not self.contract:
            if not self.load_contract():
                return []
        
        try:
            event = getattr(self.contract.events, event_name)
            # FIXED: Changed from camelCase to snake_case parameter names
            events = event.get_logs(from_block=from_block, to_block=to_block)
            return events
        except Exception as e:
            logger.error(f"Error getting events {event_name}: {e}")
            return []
    
    def get_all_events(self, from_block=0, to_block='latest'):
        """Get all events from the contract"""
        events = {}
        event_names = [
            'RoleAssigned', 'RequestCreated', 'RequestApproved',
            'StockAdjusted', 'DeliveryLogged', 'DamageReported', 'RelocationLogged'
        ]
        
        for event_name in event_names:
            events[event_name] = self.get_events(event_name, from_block, to_block)
        
        return events

# Singleton instance
web3_client = Web3Client()