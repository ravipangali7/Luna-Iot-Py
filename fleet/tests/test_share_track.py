from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from fleet.models.share_track import ShareTrack
from fleet.services.share_track_cleanup_service import ShareTrackCleanupService


class ShareTrackModelTest(TestCase):
    def setUp(self):
        self.imei = "123456789012345"
        self.token = "test_token_123"
        self.scheduled_for = timezone.now() + timedelta(hours=1)
    
    def test_create_share_track(self):
        """Test creating a share track"""
        share_track = ShareTrack.objects.create(
            imei=self.imei,
            token=self.token,
            scheduled_for=self.scheduled_for
        )
        
        self.assertEqual(share_track.imei, self.imei)
        self.assertEqual(share_track.token, self.token)
        self.assertFalse(share_track.is_expired())
    
    def test_is_expired(self):
        """Test is_expired method"""
        # Create expired share track
        expired_time = timezone.now() - timedelta(hours=1)
        expired_track = ShareTrack.objects.create(
            imei=self.imei,
            token=self.token,
            scheduled_for=expired_time
        )
        
        self.assertTrue(expired_track.is_expired())
        
        # Create active share track
        active_time = timezone.now() + timedelta(hours=1)
        active_track = ShareTrack.objects.create(
            imei="987654321098765",
            token="active_token_123",
            scheduled_for=active_time
        )
        
        self.assertFalse(active_track.is_expired())


class ShareTrackCleanupServiceTest(TestCase):
    def setUp(self):
        self.imei = "123456789012345"
        self.token = "test_token_123"
        
        # Create expired share track
        expired_time = timezone.now() - timedelta(hours=1)
        self.expired_track = ShareTrack.objects.create(
            imei=self.imei,
            token=self.token,
            scheduled_for=expired_time
        )
        
        # Create active share track
        active_time = timezone.now() + timedelta(hours=1)
        self.active_track = ShareTrack.objects.create(
            imei="987654321098765",
            token="active_token_123",
            scheduled_for=active_time
        )
    
    def test_cleanup_expired_tracks_dry_run(self):
        """Test cleanup service dry run"""
        result = ShareTrackCleanupService.cleanup_expired_tracks(dry_run=True)
        
        self.assertEqual(result['status'], 'dry_run')
        self.assertEqual(result['would_delete_count'], 1)
        self.assertEqual(ShareTrack.objects.count(), 2)  # No tracks deleted
    
    def test_cleanup_expired_tracks_actual(self):
        """Test actual cleanup of expired tracks"""
        result = ShareTrackCleanupService.cleanup_expired_tracks(dry_run=False)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['deleted_count'], 1)
        self.assertEqual(ShareTrack.objects.count(), 1)  # Only active track remains
        self.assertEqual(ShareTrack.objects.first(), self.active_track)
    
    def test_get_expired_tracks_count(self):
        """Test getting count of expired tracks"""
        count = ShareTrackCleanupService.get_expired_tracks_count()
        self.assertEqual(count, 1)
    
    def test_get_active_tracks_count(self):
        """Test getting count of active tracks"""
        count = ShareTrackCleanupService.get_active_tracks_count()
        self.assertEqual(count, 1)
    
    def test_get_all_tracks_stats(self):
        """Test getting comprehensive statistics"""
        stats = ShareTrackCleanupService.get_all_tracks_stats()
        
        self.assertEqual(stats['total_tracks'], 2)
        self.assertEqual(stats['active_tracks'], 1)
        self.assertEqual(stats['expired_tracks'], 1)
        self.assertIn('timestamp', stats)
