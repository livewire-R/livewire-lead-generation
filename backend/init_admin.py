#!/usr/bin/env python3
"""
Admin Initialization Script for SalesFuel.au

This script creates the first admin user for the SalesFuel.au platform.
Run this script once after deployment to set up the initial admin account.

Usage:
    python init_admin.py

The script will prompt for admin credentials or use environment variables:
    ADMIN_EMAIL - Admin email address
    ADMIN_PASSWORD - Admin password
    ADMIN_NAME - Admin full name
"""

import os
import sys
import getpass
import requests
import json

def get_admin_credentials():
    """Get admin credentials from environment or user input"""
    
    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD') 
    name = os.getenv('ADMIN_NAME')
    
    if not email:
        email = input("Enter admin email: ").strip()
    
    if not password:
        password = getpass.getpass("Enter admin password: ").strip()
    
    if not name:
        name = input("Enter admin full name: ").strip()
    
    return email, password, name

def create_admin_user(base_url, email, password, name):
    """Create the first admin user via API"""
    
    url = f"{base_url}/api/admin/init"
    
    payload = {
        "email": email,
        "password": password,
        "name": name
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Admin user created successfully!")
            print(f"   Email: {data['admin']['email']}")
            print(f"   Name: {data['admin']['name']}")
            print(f"   Role: {data['admin']['role']}")
            print(f"   ID: {data['admin']['id']}")
            return True
            
        elif response.status_code == 409:
            print("⚠️  Admin users already exist. Use the admin panel to manage users.")
            return False
            
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('error', f'HTTP {response.status_code}')
            print(f"❌ Failed to create admin user: {error_msg}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {base_url}")
        print("   Make sure the backend server is running.")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The server might be slow to respond.")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main function"""
    
    print("🚀 SalesFuel.au Admin Initialization")
    print("=" * 40)
    
    # Determine base URL
    base_url = os.getenv('API_BASE_URL', 'http://localhost:5000')
    
    # Check if we're in production
    if 'railway' in base_url.lower() or 'herokuapp' in base_url.lower():
        print(f"🌐 Production mode detected: {base_url}")
    else:
        print(f"🔧 Development mode: {base_url}")
    
    # Test API connection
    try:
        health_response = requests.get(f"{base_url}/api/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ API is healthy: {health_data.get('service', 'Unknown service')}")
        else:
            print(f"⚠️  API health check returned: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Could not reach API: {str(e)}")
        sys.exit(1)
    
    print()
    
    # Get admin credentials
    try:
        email, password, name = get_admin_credentials()
        
        if not email or not password or not name:
            print("❌ All fields are required.")
            sys.exit(1)
            
        # Validate email format
        if '@' not in email or '.' not in email:
            print("❌ Invalid email format.")
            sys.exit(1)
            
        # Validate password length
        if len(password) < 6:
            print("❌ Password must be at least 6 characters long.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user.")
        sys.exit(1)
    
    print()
    print("Creating admin user...")
    
    # Create admin user
    success = create_admin_user(base_url, email, password, name)
    
    if success:
        print()
        print("🎉 Setup complete!")
        print("You can now log in to the admin panel at:")
        print(f"   {base_url.replace('/api', '')}/admin")
        print()
        print("Use these credentials to log in:")
        print(f"   Email: {email}")
        print(f"   Password: [hidden]")
    else:
        print()
        print("❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

