#!/usr/bin/env python
"""
Firebase Setup Script for Luna IoT
This script helps you set up Firebase push notifications on your VPS
"""
import os
import json
from pathlib import Path

def create_firebase_setup_guide():
    """Create a guide for setting up Firebase"""
    
    print("🔥 Firebase Setup Guide for Luna IoT")
    print("=" * 50)
    print()
    
    print("📋 STEP 1: Get Firebase Service Account Key")
    print("-" * 40)
    print("1. Go to: https://console.firebase.google.com/")
    print("2. Select your project (or create one if needed)")
    print("3. Go to Project Settings (gear icon) → Service Accounts")
    print("4. Click 'Generate new private key'")
    print("5. Download the JSON file")
    print()
    
    print("📁 STEP 2: Upload to VPS")
    print("-" * 40)
    print("1. Upload the downloaded JSON file to your VPS")
    print("2. Place it in your Django project root directory")
    print("3. Rename it to: firebase-service.json")
    print("4. Set proper permissions:")
    print("   chmod 600 firebase-service.json")
    print("   chown your-user:your-group firebase-service.json")
    print()
    
    print("🔧 STEP 3: Verify Setup")
    print("-" * 40)
    print("1. Check if file exists:")
    print("   ls -la firebase-service.json")
    print("2. Verify file content:")
    print("   head -5 firebase-service.json")
    print("3. Restart your Django server:")
    print("   sudo systemctl restart gunicorn")
    print("   # or")
    print("   sudo supervisorctl restart your-app")
    print()
    
    print("✅ STEP 4: Test Notifications")
    print("-" * 40)
    print("1. Go to Django Admin Panel")
    print("2. Create a test notification")
    print("3. Check logs for success messages")
    print()
    
    print("🚨 TROUBLESHOOTING")
    print("-" * 40)
    print("If you still get 404 errors:")
    print("1. Verify the JSON file is valid:")
    print("   python -c \"import json; json.load(open('firebase-service.json'))\"")
    print("2. Check file permissions:")
    print("   ls -la firebase-service.json")
    print("3. Ensure the file is in the correct location")
    print("4. Check Django logs for detailed error messages")
    print()
    
    print("📱 FCM Token Setup")
    print("-" * 40)
    print("For users to receive notifications:")
    print("1. Users must login through the Flutter app")
    print("2. The app will automatically register FCM tokens")
    print("3. Tokens are stored in the user.fcm_token field")
    print("4. Only users with valid FCM tokens will receive push notifications")
    print()
    
    print("🔒 SECURITY NOTES")
    print("-" * 40)
    print("1. Never commit firebase-service.json to version control")
    print("2. Add it to .gitignore:")
    print("   echo 'firebase-service.json' >> .gitignore")
    print("3. Keep the file secure with proper permissions")
    print("4. Consider using environment variables for production")
    print()

def check_current_setup():
    """Check current Firebase setup"""
    print("🔍 Checking Current Firebase Setup")
    print("=" * 40)
    
    # Check if firebase-service.json exists
    firebase_file = Path("firebase-service.json")
    if firebase_file.exists():
        print("✅ firebase-service.json found")
        try:
            with open(firebase_file, 'r') as f:
                data = json.load(f)
            print("✅ JSON file is valid")
            print(f"📧 Project ID: {data.get('project_id', 'Not found')}")
            print(f"🔑 Client Email: {data.get('client_email', 'Not found')}")
        except Exception as e:
            print(f"❌ JSON file is invalid: {e}")
    else:
        print("❌ firebase-service.json not found")
        print("   Please follow the setup guide above")
    
    print()
    
    # Check if firebase-admin is installed
    try:
        import firebase_admin
        print(f"✅ firebase-admin installed (version: {firebase_admin.__version__})")
    except ImportError:
        print("❌ firebase-admin not installed")
        print("   Run: pip install firebase-admin==6.4.0")
    
    print()

if __name__ == "__main__":
    check_current_setup()
    create_firebase_setup_guide()
    
    print("🎯 QUICK FIX")
    print("=" * 40)
    print("If you want to temporarily disable push notifications:")
    print("1. The code has been updated to handle missing Firebase gracefully")
    print("2. Notifications will be saved to database but not sent as push notifications")
    print("3. Users can still see notifications in the app")
    print("4. No more 404 errors will occur")
    print()
    print("To enable push notifications later, just add the firebase-service.json file")
    print("and restart your Django server.")
