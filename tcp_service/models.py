from django.db import models


class DashcamLocation(models.Model):
    """
    Stores GPS location data from dashcam devices (JT808 protocol).
    Uses deduplication logic: only insert if data changed, otherwise update timestamp.
    """
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, db_index=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.IntegerField(default=0)
    speed = models.FloatField(default=0)  # km/h
    direction = models.IntegerField(default=0)  # 0-360 degrees
    satellite = models.IntegerField(default=0)
    alarm_flags = models.BigIntegerField(default=0)
    status_flags = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'dashcam_locations'
        indexes = [
            models.Index(fields=['imei']),
            models.Index(fields=['imei', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"DashcamLocation {self.imei} ({self.latitude}, {self.longitude})"


class DashcamStatus(models.Model):
    """
    Stores device status data from dashcam devices.
    Tracks battery, signal, recording status, SD card status, and camera health.
    """
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, db_index=True)
    battery = models.IntegerField(default=0)  # 0-100 percentage
    signal = models.IntegerField(default=0)  # Signal strength
    recording = models.BooleanField(default=False)
    sd_status = models.CharField(max_length=20, default='unknown')  # ok/error/full/missing
    front_camera = models.BooleanField(default=True)
    rear_camera = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'dashcam_statuses'
        indexes = [
            models.Index(fields=['imei']),
            models.Index(fields=['imei', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"DashcamStatus {self.imei} (Battery: {self.battery}%)"


class DashcamStream(models.Model):
    """
    Tracks active video streaming sessions from dashcam devices.
    """
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, db_index=True)
    channel = models.IntegerField(default=1)  # 1=Front, 2=Rear
    is_streaming = models.BooleanField(default=False)
    stream_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    codec = models.CharField(max_length=20, default='avc1.640028')
    width = models.IntegerField(default=1280)
    height = models.IntegerField(default=720)
    fps = models.IntegerField(default=25)
    viewer_count = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'dashcam_streams'
        indexes = [
            models.Index(fields=['imei']),
            models.Index(fields=['imei', 'channel']),
            models.Index(fields=['stream_key']),
        ]

    def __str__(self):
        status = "Streaming" if self.is_streaming else "Idle"
        channel_name = "Front" if self.channel == 1 else "Rear"
        return f"DashcamStream {self.imei} Ch{self.channel} ({channel_name}) - {status}"


class DashcamConnection(models.Model):
    """
    Tracks connected dashcam devices and their connection state.
    """
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    auth_code = models.CharField(max_length=32, blank=True, default='')
    is_connected = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    connected_at = models.DateTimeField(null=True, blank=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'dashcam_connections'
        indexes = [
            models.Index(fields=['imei']),
            models.Index(fields=['is_connected']),
        ]

    def __str__(self):
        status = "Connected" if self.is_connected else "Disconnected"
        return f"DashcamConnection {self.imei} - {status}"
