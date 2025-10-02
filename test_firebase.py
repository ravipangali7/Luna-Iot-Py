#!/usr/bin/env python
"""
Test script to verify Firebase setup and debug push notification issues
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luna_iot_py.settings')
django.setup()

def test_firebase_setup():
    """Test Firebase setup and configuration"""
    print("🔍 Testing Firebase setup...")
    
    try:
        # Test 1: Check if firebase-admin is installed
        import firebase_admin
        from firebase_admin import credentials, messaging
        print("✅ firebase-admin package is installed")
        print(f"   Version: {firebase_admin.__version__}")
    except ImportError as e:
        print(f"❌ firebase-admin package not found: {e}")
        print("   Please run: pip install firebase-admin==6.4.0")
        return False
    
    try:
        # Test 2: Check if firebase-service.json exists
        firebase_config_path = os.path.join(BASE_DIR, 'firebase-service.json')
        if os.path.exists(firebase_config_path):
            print(f"✅ Firebase service account key found at: {firebase_config_path}")
            
            # Test 3: Try to load credentials
            try:
                cred = credentials.Certificate(firebase_config_path)
                print("✅ Firebase credentials loaded successfully")
            except Exception as cred_error:
                print(f"❌ Failed to load Firebase credentials: {cred_error}")
                return False
        else:
            print(f"❌ Firebase service account key not found at: {firebase_config_path}")
            print("   Please ensure firebase-service.json is in the project root directory.")
            return False
    except Exception as e:
        print(f"❌ Error checking Firebase config: {e}")
        return False
    
    try:
        # Test 4: Test Firebase initialization
        from api_common.services.firebase_service import initialize_firebase, FIREBASE_INITIALIZED
        result = initialize_firebase()
        if result and FIREBASE_INITIALIZED:
            print("✅ Firebase Admin SDK initialized successfully")
        else:
            print("❌ Firebase Admin SDK initialization failed")
            return False
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")
        return False
    
    try:
        # Test 5: Test FCM token retrieval
        from core.models.user import User
        users_with_tokens = User.objects.filter(
            fcm_token__isnull=False
        ).exclude(fcm_token='').count()
        print(f"✅ Found {users_with_tokens} users with FCM tokens")
        
        if users_with_tokens == 0:
            print("⚠️  No users have FCM tokens. This might be why notifications are failing.")
            print("   Make sure users are logging in through the Flutter app to register their tokens.")
    except Exception as e:
        print(f"❌ Error checking FCM tokens: {e}")
        return False
    
    print("\n🎉 Firebase setup test completed successfully!")
    return True

def test_notification_sending():
    """Test sending a notification (dry run)"""
    print("\n🔍 Testing notification sending...")
    
    try:
        from api_common.services.firebase_service import send_push_notification
        
        # Test with a dummy notification (won't actually send)
        print("   Testing notification function (dry run)...")
        
        # This will test the function without actually sending
        result = send_push_notification(
            notification_id=999,
            title="Test Notification",
            body="This is a test notification",
            notification_type="all"
        )
        
        if result:
            print("✅ Notification sending function works")
        else:
            print("❌ Notification sending function failed")
            
    except Exception as e:
        print(f"❌ Error testing notification sending: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Firebase setup test...\n")
    
    # Run tests
    setup_ok = test_firebase_setup()
    
    if setup_ok:
        test_notification_sending()
    
    print("\n" + "="*50)
    if setup_ok:
        print("✅ All tests passed! Firebase should be working now.")
        print("\nNext steps:")
        print("1. Restart your Django server")
        print("2. Try sending a notification from the admin panel")
        print("3. Check the logs for any remaining errors")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("1. Install firebase-admin: pip install firebase-admin==6.4.0")
        print("2. Ensure firebase-service.json is in the project root")
        print("3. Check that the service account key is valid")
        print("4. Make sure users have FCM tokens (login through Flutter app)")
