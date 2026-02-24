# 
Spyglass Application Initialization Module
Handles admin privileges, device information retrieval, and database setup on first launch
# 

import sys
from typing import bool_

from adminHandler import AdminHandler
from userInfo import DeviceInfo
from database import DatabaseManager


class SpyglassInitializer:
    # Initialize Spyglass application with required permissions and device info# 
    
    def __init__(self):
        self.adminHandler = None
        self.userInfo = None
        self.database = None
        self.user_id = None
    
    def initialize(self) -> bool:
        # Run full initialization sequence# 
        print("="*60)
        print("SPYGLASS APPLICATION INITIALIZATION".center(60))
        print("="*60)
        
        # Step 1: Request admin privileges
        print("\n[Step 1/4] Checking Administrator Privileges...")
        if not self._request_admin_privileges():
            print("ERROR: Failed to obtain administrator privileges.")
            return False
        
        # Step 2: Initialize database
        print("\n[Step 2/4] Initializing Database...")
        if not self._initialize_database():
            print("ERROR: Failed to initialize database.")
            return False
        
        # Step 3: Retrieve device information
        print("\n[Step 3/4] Gathering Device Information...")
        if not self._retrieve_userInfo():
            print("ERROR: Failed to retrieve device information.")
            return False
        
        # Step 4: Store device information in database
        print("\n[Step 4/4] Storing Device Information...")
        if not self._store_userInfo():
            print("ERROR: Failed to store device information.")
            return False
        
        print("\n" + "="*60)
        print("INITIALIZATION SUCCESSFUL".center(60))
        print("="*60 + "\n")
        
        return True
    
    def _request_admin_privileges(self) -> bool:
        # Request and verify administrator privileges# 
        try:
            self.adminHandler = AdminHandler()
            print(f"Current privilege level: {self.adminHandler.get_status()}")
            
            if not self.adminHandler.verify_admin_status():
                return False
            
            print("Administrator privileges confirmed.")
            return True
        except Exception as e:
            print(f"Error checking admin privileges: {e}")
            return False
    
    def _initialize_database(self) -> bool:
        # Initialize the database with SQLCipher encryption# 
        try:
            # Generate encryption key from machine identifier
            # In production, this should be more robust
            import hashlib
            defaultKey = hashlib.sha256(b"spyglass_secure_key_v1").hexdigest()
            
            self.database = DatabaseManager()
            self.database.initializeDB(create_tables=True, encryption_key=defaultKey)
            
            if not self.database.verifyConnection():
                return False
            
            print("Database initialized with SQLCipher encryption and verified.")
            return True
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False
    
    def _retrieve_userInfo(self) -> bool:
        # Retrieve device information# 
        try:
            self.userInfo = DeviceInfo()
            
            # Print summary for user
            self.userInfo.print_summary()
            
            print("Device information retrieved successfully.")
            return True
        except Exception as e:
            print(f"Error retrieving device information: {e}")
            return False
    
    def _store_userInfo(self) -> bool:
        # Store device information in database# 
        try:
            if self.userInfo is None or self.database is None:
                print("Device info or database not initialized.")
                return False
            
            # For now, use user_id = 1 (default admin user)
            # In a real app, this would be determined by login/configuration
            self.user_id = 1
            
            success = self.database.storeDeviceInfo(
                self.user_id,
                self.userInfo.to_dict()
            )
            
            if success:
                print("Device information stored in database.")
            return success
        except Exception as e:
            print(f"Error storing device information: {e}")
            return False
    
    def get_userInfo(self) -> dict:
        # Get the stored device information# 
        if self.userInfo:
            return self.userInfo.to_dict()
        return {}
    
    def cleanup(self) -> None:
        # Clean up resources# 
        if self.database:
            self.database.closeDB()


def run_initialization():
    # Run the initialization process# 
    initializer = SpyglassInitializer()
    
    try:
        success = initializer.initialize()
        if success:
            print("\nSpyglass is ready to use!")
            return initializer
        else:
            print("\nInitialization failed. Please check the errors above.")
            initializer.cleanup()
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during initialization: {e}")
        initializer.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    initializer = run_initialization()
