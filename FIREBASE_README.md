# Firebase Setup

## Configuration

Update these values in `luna_iot_py/settings.py`:

```python
# Firebase Configuration
FIREBASE_PROJECT_ID = 'your-firebase-project-id'
FIREBASE_CLIENT_EMAIL = 'your-service-account@your-project.iam.gserviceaccount.com'
FIREBASE_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nYour-Private-Key-Here\n-----END PRIVATE KEY-----\n'
```

## How to Get These Values

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to Project Settings > Service Accounts
4. Click "Generate new private key"
5. Download the JSON file
6. Copy the values from the JSON file to your `settings.py` file

## Installation

```bash
pip install firebase-admin==6.5.0
```
