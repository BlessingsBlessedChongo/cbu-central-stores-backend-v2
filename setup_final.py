#!/usr/bin/env python3
"""
CBU Central Stores Final Setup Script
Run this script to verify everything is working correctly
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'central_stores.settings')
django.setup()

def run_checks():
    """Run comprehensive system checks"""
    print("🚀 Running Final System Checks...")
    
    # Test database connection
    try:
        from django.db import connection
        connection.ensure_connection()
        print("✅ Database connection: OK")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test blockchain connection
    try:
        from core.web3_client import web3_client
        if web3_client.is_connected():
            print("✅ Blockchain connection: OK")
        else:
            print("❌ Blockchain connection failed")
            return False
    except Exception as e:
        print(f"❌ Blockchain connection failed: {e}")
        return False
    
    # Test contract loading
    try:
        if web3_client.contract:
            info = web3_client.get_contract_info()
            print(f"✅ Contract loaded: {info}")
        else:
            print("❌ Contract not loaded")
            return False
    except Exception as e:
        print(f"❌ Contract loading failed: {e}")
        return False
    
    # Test encryption
    try:
        from core.encryption import encrypt_data, decrypt_data
        test_data = "test_secret_data"
        encrypted = encrypt_data(test_data)
        decrypted = decrypt_data(encrypted)
        if decrypted == test_data:
            print("✅ Encryption/Decryption: OK")
        else:
            print("❌ Encryption/Decryption failed")
            return False
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        return False
    
    print("🎉 All systems are ready for production!")
    return True

if __name__ == "__main__":
    if run_checks():
        sys.exit(0)
    else:
        sys.exit(1)