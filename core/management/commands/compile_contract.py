import json
import os
from solcx import compile_standard, install_solc
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Compile the StreamlinedStoresManagerV3 smart contract'
    
    def handle(self, *args, **options):
        self.stdout.write('Installing Solidity compiler...')
        install_solc('0.8.19')
        
        contract_path = os.path.join(settings.BASE_DIR, 'contracts', 'StreamlinedStoresManagerV3.sol')
        
        with open(contract_path, 'r') as file:
            contract_source = file.read()
        
        compiled_sol = compile_standard({
            "language": "Solidity",
            "sources": {
                "StreamlinedStoresManagerV3.sol": {
                    "content": contract_source
                }
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            }
        }, solc_version="0.8.19")
        
        # Create build directory if it doesn't exist
        build_dir = os.path.join(settings.BASE_DIR, 'contracts', 'build')
        os.makedirs(build_dir, exist_ok=True)
        
        # Save compiled contract
        compiled_path = os.path.join(build_dir, 'compiled_contract.json')
        with open(compiled_path, 'w') as file:
            json.dump(compiled_sol, file, indent=4)
        
        # Save ABI separately
        abi = compiled_sol['contracts']['StreamlinedStoresManagerV3.sol']['StreamlinedStoresManagerV3']['abi']
        abi_path = os.path.join(build_dir, 'abi.json')
        with open(abi_path, 'w') as file:
            json.dump(abi, file, indent=4)
        
        self.stdout.write(
            self.style.SUCCESS('Contract compiled successfully!')
        )
        self.stdout.write(f'ABI saved to: {abi_path}')
        self.stdout.write(f'Full compilation saved to: {compiled_path}')