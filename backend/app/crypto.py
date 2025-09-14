import os
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from typing import Tuple, Dict, Any
import json


class CryptoManager:
    """Handles all cryptographic operations for E2EE"""
    
    @staticmethod
    def generate_rsa_keypair() -> Tuple[str, str]:
        """Generate RSA key pair for user"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem.decode('utf-8'), public_pem.decode('utf-8')
    
    @staticmethod
    def encrypt_private_key(private_key_pem: str, password: str, salt: bytes = None) -> Tuple[str, str]:
        """Encrypt user's private key with password"""
        if salt is None:
            salt = os.urandom(16)
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        
        # Encrypt private key
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad the private key
        private_key_bytes = private_key_pem.encode()
        padding_length = 16 - (len(private_key_bytes) % 16)
        padded_data = private_key_bytes + bytes([padding_length] * padding_length)
        
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine salt, iv, and encrypted data
        result = salt + iv + encrypted_data
        return base64.b64encode(result).decode('utf-8'), base64.b64encode(salt).decode('utf-8')
    
    @staticmethod
    def decrypt_private_key(encrypted_private_key: str, password: str) -> str:
        """Decrypt user's private key with password"""
        encrypted_data = base64.b64decode(encrypted_private_key.encode())
        
        # Extract salt, iv, and encrypted key
        salt = encrypted_data[:16]
        iv = encrypted_data[16:32]
        encrypted_key = encrypted_data[32:]
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        
        # Decrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_key) + decryptor.finalize()
        
        # Remove padding
        padding_length = padded_data[-1]
        private_key_bytes = padded_data[:-padding_length]
        
        return private_key_bytes.decode()
    
    @staticmethod
    def generate_sheet_key() -> str:
        """Generate AES key for sheet encryption"""
        key = os.urandom(32)  # 256-bit key
        return base64.b64encode(key).decode('utf-8')
    
    @staticmethod
    def encrypt_with_public_key(data: str, public_key_pem: str) -> str:
        """Encrypt data with RSA public key"""
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        encrypted = public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt_with_private_key(encrypted_data: str, private_key_pem: str) -> str:
        """Decrypt data with RSA private key"""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted.decode()
    
    @staticmethod
    def encrypt_sheet_data(data: Dict[str, Any], sheet_key: str) -> str:
        """Encrypt sheet data with AES"""
        key = base64.b64decode(sheet_key.encode())
        iv = os.urandom(16)
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Convert data to JSON and encode
        json_data = json.dumps(data).encode()
        
        # Pad data
        padding_length = 16 - (len(json_data) % 16)
        padded_data = json_data + bytes([padding_length] * padding_length)
        
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and encrypted data
        result = iv + encrypted_data
        return base64.b64encode(result).decode('utf-8')
    
    @staticmethod
    def decrypt_sheet_data(encrypted_data: str, sheet_key: str) -> Dict[str, Any]:
        """Decrypt sheet data with AES"""
        key = base64.b64decode(sheet_key.encode())
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        
        # Extract IV and encrypted data
        iv = encrypted_bytes[:16]
        encrypted_content = encrypted_bytes[16:]
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_content) + decryptor.finalize()
        
        # Remove padding
        padding_length = padded_data[-1]
        json_data = padded_data[:-padding_length]
        
        return json.loads(json_data.decode())
    
    @staticmethod
    def encrypt_cell_value(value: str, sheet_key: str) -> str:
        """Encrypt individual cell value"""
        if not value or value.strip() == "":
            return value
        
        # For individual cells, we'll use a simpler approach
        data = {"value": value, "type": "cell"}
        return CryptoManager.encrypt_sheet_data(data, sheet_key)
    
    @staticmethod
    def decrypt_cell_value(encrypted_value: str, sheet_key: str) -> str:
        """Decrypt individual cell value"""
        if not encrypted_value or encrypted_value.strip() == "":
            return encrypted_value
        
        try:
            data = CryptoManager.decrypt_sheet_data(encrypted_value, sheet_key)
            return data.get("value", "")
        except:
            # If decryption fails, return original value (might be unencrypted)
            return encrypted_value
