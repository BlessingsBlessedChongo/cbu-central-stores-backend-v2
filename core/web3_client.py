import os
import json
from web3 import Web3
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

class Web3Client:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URI', 'http://127.0.0.1:7545')))
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.contract = None
        
        if self.contract_address:
            self.load_contract()
    
    def load_contract(self):
        """Load the deployed contract"""
        if not self.contract_address:
            raise ValueError("Contract address not set in environment variables")
        
        # Load ABI
        abi_path = os.path.join(settings.BASE_DIR, 'contracts', 'build', 'abi.json')
        with open(abi_path, 'r') as file:
            contract_abi = json.load(file)
        
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=contract_abi
        )
    
    def is_connected(self):
        """Check if connected to blockchain"""
        return self.w3.is_connected()
    
    def get_contract_info(self):
        """Get contract information"""
        if not self.contract:
            self.load_contract()
        
        return self.contract.functions.getContractInfo().call()
    
    def get_contract_instance(self):
        """Get the contract instance"""
        if not self.contract:
            self.load_contract()
        
        return self.contract