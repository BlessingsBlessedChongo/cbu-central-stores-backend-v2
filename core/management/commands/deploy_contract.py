import json
import os
from web3 import Web3
from django.core.management.base import BaseCommand
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

class Command(BaseCommand):
    help = 'Deploy the StreamlinedStoresManagerV3 smart contract to Ganache'
    
    def handle(self, *args, **options):
        # Load compiled contract
        build_dir = os.path.join(settings.BASE_DIR, 'contracts', 'build')
        compiled_path = os.path.join(build_dir, 'compiled_contract.json')
        
        with open(compiled_path, 'r') as file:
            compiled_sol = json.load(file)
        
        # Get contract ABI and bytecode
        contract_abi = compiled_sol['contracts']['StreamlinedStoresManagerV3.sol']['StreamlinedStoresManagerV3']['abi']
        contract_bytecode = compiled_sol['contracts']['StreamlinedStoresManagerV3.sol']['StreamlinedStoresManagerV3']['evm']['bytecode']['object']
        
        # Connect to Ganache
        w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URI', 'http://127.0.0.1:7545')))
        
        if not w3.is_connected():
            self.stdout.write(self.style.ERROR('Could not connect to Ganache. Make sure it\'s running on http://127.0.0.1:7545'))
            return
        
        # Get account for deployment
        account_address = os.getenv('DEPLOYER_ACCOUNT_ADDRESS')
        private_key = os.getenv('DEPLOYER_PRIVATE_KEY')
        
        if not account_address or not private_key:
            self.stdout.write(self.style.ERROR('DEPLOYER_ACCOUNT_ADDRESS and DEPLOYER_PRIVATE_KEY must be set in .env'))
            return
        
        # Create contract instance
        Contract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
        
        # Get nonce
        nonce = w3.eth.get_transaction_count(account_address)
        
        # Build transaction
        transaction = Contract.constructor().build_transaction({
            'chainId': 1337,  # Ganache chain ID
            'gas': 3000000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'from': account_address,  # Added from address for clarity
        })
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
        
        # Send transaction - FIXED: Use raw_transaction instead of rawTransaction
        self.stdout.write('Deploying contract...')
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Fixed attribute name
        
        # Wait for transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Save contract address to .env
        contract_address = tx_receipt.contractAddress
        
        # Update .env file
        env_path = os.path.join(settings.BASE_DIR, '.env')
        env_lines = []
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as file:
                env_lines = file.readlines()
        
        # Update or add CONTRACT_ADDRESS
        contract_found = False
        for i, line in enumerate(env_lines):
            if line.startswith('CONTRACT_ADDRESS='):
                env_lines[i] = f'CONTRACT_ADDRESS={contract_address}\n'
                contract_found = True
                break
        
        if not contract_found:
            env_lines.append(f'CONTRACT_ADDRESS={contract_address}\n')
        
        with open(env_path, 'w') as file:
            file.writelines(env_lines)
        
        self.stdout.write(self.style.SUCCESS(
            f'Contract deployed successfully!\n'
            f'Contract address: {contract_address}\n'
            f'Transaction hash: {tx_hash.hex()}'
        ))