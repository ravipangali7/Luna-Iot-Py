# Alert SMS Notifications

This document describes the SMS notification system implemented for the alert system.

## Overview

The SMS notification system automatically sends SMS messages when:
1. A new alert is created (to alert contacts and activates buzzers)
2. An alert's status or remarks are updated (to the alert sender)

## Features

### 1. Alert Creation Notifications
When a new alert is created:
- **SMS to Alert Contacts**: Sends SMS to all matching alert contacts
- **Buzzer Activation**: Sends relay ON command to matching buzzers
- **Automatic Relay OFF**: Schedules relay OFF command after buzzer's delay period

### 2. Alert Update Notifications
When an alert's status or remarks are updated:
- **Acceptance SMS**: Sends SMS to the alert sender's primary phone

## Implementation Files

### Core Service
- `services/alert_sms_service.py` - Main SMS service with all notification logic

### Background Tasks
- `tasks.py` - Celery tasks for delayed operations (relay OFF commands)

### Signal Handlers
- `signals.py` - Django signals that trigger SMS notifications

### Test Script
- `test_sms_notifications.py` - Test script to verify functionality

## SMS Message Templates

### Alert to Contacts
```
"{alert_history.name}, need your help for {alert_type.name}. Contact on {alert_history.primary_phone}."
```

### Acceptance to Alert Sender
```
"{institute.name} accepted help for your {alert_type.name}"
```

## Contact Matching Logic

Alert contacts are matched based on:
1. **Institute**: Must match the alert's institute
2. **Geofences**: Alert location must be inside contact's geofences (or no geofence restriction)
3. **Alert Types**: Contact must be associated with the alert type (or no type restriction)
4. **SMS Enabled**: `is_sms=True`

## Buzzer Matching Logic

Buzzers are activated based on:
1. **Institute**: Must match the alert's institute
2. **Geofences**: Alert location must be inside buzzer's geofences

## Relay Commands

### Relay ON Command
```
RELAY,1#
```

### Relay OFF Command
```
RELAY,0#
```

## Configuration

### SMS Service
The SMS service uses the existing `api_common.utils.sms_service` with these settings:
- API Key: `SMS_API_KEY`
- API URL: `SMS_API_URL`
- Campaign ID: `SMS_CAMPAIGN_ID`
- Route ID: `SMS_ROUTE_ID`
- Sender ID: `SMS_SENDER_ID`

### Background Tasks
Uses Celery for background task processing. If Celery is not available, falls back to threading.

## Usage

### Automatic Notifications
SMS notifications are sent automatically via Django signals when:
- AlertHistory instances are created or updated

### Manual Testing
Run the test script to verify functionality:
```bash
cd Luna-Iot-Py
python alert_system/test_sms_notifications.py
```

## Dependencies

- Django signals (post_save, pre_save)
- Celery (for background tasks)
- Existing SMS service (`api_common.utils.sms_service`)
- Geofence point-in-polygon logic (`alert_notification_service.is_point_in_polygon`)

## Error Handling

- All SMS operations are wrapped in try-catch blocks
- Failed SMS sends are logged but don't prevent other operations
- Background tasks have error handling and logging
- Signal handlers have comprehensive error handling

## Logging

All operations are logged with appropriate levels:
- INFO: Successful operations
- WARNING: Failed operations that don't break the flow
- ERROR: Critical errors that need attention

## Database Models Used

- `AlertHistory` - Main alert records
- `AlertContact` - Contact information and preferences
- `AlertBuzzer` - Buzzer devices and their geofences
- `AlertGeofence` - Geofence boundaries
- `AlertType` - Alert type definitions
- `Institute` - Institute information
- `Device` - Device information (for buzzer phone numbers)
