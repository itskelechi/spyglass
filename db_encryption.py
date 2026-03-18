# 
#Database Encryption Utilities
# Provides encryption and decryption functions for database security
# 

import os
from cryptography.fernet import Fernet
from typing import Optional


class DatabaseEncryption:
    # Handle encryption/decryption of database files# 
    
    def __init__(self, key_file: str = ".spyglass_key"):
        self.key_file = key_file
        self.key = None
        self._load_or_create_key()
    
    def _load_or_create_key(self) -> None:
        # Load existing key or create a new one# 
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            self._save_key(self.key)
    
    def _save_key(self, key: bytes) -> None:
        # Save encryption key to file# 
        try:
            # Make key file read-only
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)  # Read-write for owner only
            print(f"Encryption key saved to {self.key_file}")
        except Exception as e:
            print(f"Error saving encryption key: {e}")
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> bool:
        # Encrypt a file using Fernet encryption# 
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
        
        if output_path is None:
            output_path = f"{file_path}.encrypted"
        
        try:
            cipher = Fernet(self.key)
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = cipher.encrypt(file_data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"File encrypted successfully: {output_path}")
            return True
        except Exception as e:
            print(f"Error encrypting file: {e}")
            return False
    
    def decrypt_file(self, file_path: str, output_path: Optional[str] = None) -> bool:
        # Decrypt a file using Fernet decryption# 
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
        
        if output_path is None:
            output_path = file_path.replace(".encrypted", ".decrypted")
        
        try:
            cipher = Fernet(self.key)
            
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = cipher.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"File decrypted successfully: {output_path}")
            return True
        except Exception as e:
            print(f"Error decrypting file: {e}")
            return False
    
    def backup_database(self, db_path: str, backup_dir: str = "backups") -> bool:
        # Create an encrypted backup of the database# 
        try:
            import shutil
            from datetime import datetime
            
            # Create backup directory
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                print(f"Created backup directory: {backup_dir}")
            
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"spyglass_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy database
            shutil.copy2(db_path, backup_path)
            print(f"Database backed up to: {backup_path}")
            
            # Encrypt backup
            encrypted_backup = f"{backup_path}.encrypted"
            success = self.encrypt_file(backup_path, encrypted_backup)
            
            if success:
                # Remove unencrypted backup
                os.remove(backup_path)
                print(f"Unencrypted backup removed. Encrypted version saved: {encrypted_backup}")
            
            return success
        except Exception as e:
            print(f"Error backing up database: {e}")
            return False
    
    def restore_database(self, backup_path: str, db_path: str) -> bool:
        # Restore database from encrypted backup# 
        try:
            import shutil
            
            # Check if backup is encrypted
            if backup_path.endswith(".encrypted"):
                # Decrypt first
                decrypted_path = backup_path.replace(".encrypted", ".temp")
                if not self.decrypt_file(backup_path, decrypted_path):
                    return False
                backup_to_restore = decrypted_path
            else:
                backup_to_restore = backup_path
            
            # Restore database
            shutil.copy2(backup_to_restore, db_path)
            print(f"Database restored from: {backup_path}")
            
            # Clean up temporary decrypted file
            if backup_path.endswith(".encrypted"):
                os.remove(backup_to_restore)
            
            return True
        except Exception as e:
            print(f"Error restoring database: {e}")
            return False
    
    def get_key_fingerprint(self) -> str:
        # Get a fingerprint of the encryption key for verification# 
        import hashlib
        
        key_hash = hashlib.sha256(self.key).hexdigest()
        return key_hash[:16]  # Return first 16 chars


def secure_delete_file(file_path: str, passes: int = 3) -> bool:
    # Securely delete a file by overwriting it multiple times# 
    try:
        file_size = os.path.getsize(file_path)
        
        # Overwrite file multiple times
        for _ in range(passes):
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
        
        # Finally delete
        os.remove(file_path)
        print(f"File securely deleted: {file_path}")
        return True
    except Exception as e:
        print(f"Error securely deleting file: {e}")
        return False
