from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os

def get_fernet_key():
    """Get or create Fernet key from environment variable"""
    fernet_key = os.getenv('FERNET_KEY')
    if not fernet_key:
        # Generate new key if not exists
        fernet_key = Fernet.generate_key().decode()
        # Update .env file (for development)
        try:
            env_path = os.path.join(settings.BASE_DIR, '.env')
            with open(env_path, 'a') as f:
                f.write(f'\nFERNET_KEY={fernet_key}\n')
        except:
            pass
    return fernet_key

def encrypt_data(data):
    """Encrypt data using Fernet"""
    if not data:
        return None
    fernet = Fernet(get_fernet_key())
    encrypted_data = fernet.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()

def decrypt_data(encrypted_data):
    """Decrypt data using Fernet"""
    if not encrypted_data:
        return None
    try:
        fernet = Fernet(get_fernet_key())
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(decoded_data).decode()
        return decrypted_data
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

# Add encryption methods to CustomUser model
def encrypt_private_key(self, private_key):
    """Encrypt and store private key"""
    if private_key:
        self.encrypted_private_key = encrypt_data(private_key)
        self.save()

def decrypt_private_key(self):
    """Decrypt and return private key"""
    return decrypt_data(self.encrypted_private_key)

# Add methods to CustomUser model
from .models import CustomUser
CustomUser.encrypt_private_key = encrypt_private_key
CustomUser.decrypt_private_key = decrypt_private_key