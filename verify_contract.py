import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'central_stores.settings')
django.setup()

from core.web3_client import Web3Client

def test_connection():
    client = Web3Client()
    print(f"Connected to blockchain: {client.is_connected()}")
    
    if client.contract_address:
        print(f"Contract address: {client.contract_address}")
        print(f"Contract info: {client.get_contract_info()}")
    else:
        print("Contract not deployed yet")

if __name__ == '__main__':
    test_connection()