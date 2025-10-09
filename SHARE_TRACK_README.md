# Share Track Feature Documentation

## Overview
The Share Track feature allows users to create temporary shareable links for vehicle tracking that automatically expire after a specified duration. This is useful for sharing live vehicle location with clients, family members, or other stakeholders without giving them permanent access.

## Features
- Create shareable links with customizable expiration times (10 minutes to 24 hours)
- Automatic cleanup of expired share tracks
- Secure token-based sharing
- User-friendly modal interface
- API endpoints for programmatic access

## Backend Components

### 1. Model (`fleet/models/share_track.py`)
```python
class ShareTrack(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    imei = models.CharField(max_length=100, unique=True)
    token = models.CharField(max_length=32, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(help_text="Time when the share link expires")
```

### 2. API Endpoints
- `POST /api/fleet/share-track/create` - Create a new share track
- `GET /api/fleet/share-track/existing/:imei` - Get existing share track for IMEI
- `DELETE /api/fleet/share-track/delete/:imei` - Delete share track for IMEI
- `GET /api/fleet/share-track/my-tracks` - Get all user's share tracks
- `GET /api/fleet/share-track/:token` - Get share track by token (public)

### 3. Cleanup Service
The system automatically cleans up expired share tracks through multiple methods:

#### Management Command
```bash
# Run cleanup manually
python manage.py cleanup_expired_share_tracks

# Dry run to see what would be deleted
python manage.py cleanup_expired_share_tracks --dry-run --verbose
```

#### Celery Task (Recommended)
```python
# Add to your Celery Beat schedule
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-share-tracks': {
        'task': 'fleet.tasks.cleanup_expired_share_tracks',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
}
```

#### Service Class
```python
from fleet.services.share_track_cleanup_service import ShareTrackCleanupService

# Manual cleanup
result = ShareTrackCleanupService.cleanup_expired_tracks()

# Get statistics
stats = ShareTrackCleanupService.get_all_tracks_stats()
```

## Frontend Components

### 1. Share Track Modal (`lib/widgets/vehicle/share_track_modal.dart`)
- User-friendly interface for creating share tracks
- Duration selection buttons (10 min, 30 min, 1 hour, 2 hours, 12 hours, 24 hours)
- Copy to clipboard functionality
- Shows existing share links if available

### 2. API Service (`lib/api/services/share_track_api_service.dart`)
- Handles all API communication
- Error handling and response parsing
- Integration with existing API client

### 3. Integration
The share track button is integrated into the live tracking screen (`vehicle_live_tracking_show_screen.dart`).

## Usage

### Creating a Share Track
1. Open the live tracking screen for a vehicle
2. Tap the purple share button
3. Select desired duration from the modal
4. Copy the generated link to share

### API Usage
```dart
// Create a share track
final result = await shareTrackApiService.createShareTrack(
  '123456789012345',
  60, // 60 minutes
);

// Get existing share track
final existing = await shareTrackApiService.getExistingShare('123456789012345');
```

## Security Considerations
- Tokens are generated using `secrets.token_urlsafe(16)` for security
- Share tracks are automatically cleaned up to prevent data accumulation
- No authentication required for public share links (by design)
- IMEI validation ensures only valid vehicles can be shared

## Database Migration
After implementing the feature, run:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Monitoring
- Check logs for cleanup operations
- Monitor database size for share_track table
- Use the management command to verify cleanup is working

## Troubleshooting

### Common Issues
1. **Share track not created**: Check if vehicle exists and user has permissions
2. **Cleanup not working**: Verify Celery Beat is running and tasks are scheduled
3. **API errors**: Check authentication and request format

### Debug Commands
```bash
# Check expired tracks
python manage.py cleanup_expired_share_tracks --dry-run --verbose

# Test Celery task
python manage.py shell
>>> from fleet.tasks import cleanup_expired_share_tracks
>>> cleanup_expired_share_tracks.delay()
```

## Future Enhancements
- Email notifications when share tracks are created
- Web interface for managing share tracks
- Analytics on share track usage
- Custom expiration times beyond the predefined options
