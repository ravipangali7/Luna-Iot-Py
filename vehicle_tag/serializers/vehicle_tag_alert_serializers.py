"""
Vehicle Tag Alert Serializers
Handles serialization for vehicle tag alert endpoints
"""
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from vehicle_tag.models import VehicleTagAlert


class VehicleTagAlertSerializer(serializers.ModelSerializer):
    """Serializer for vehicle tag alert model"""
    vehicle_tag_vtid = serializers.CharField(source='vehicle_tag.vtid', read_only=True)
    vehicle_tag_registration_no = serializers.CharField(source='vehicle_tag.registration_no', read_only=True)
    alert_display = serializers.CharField(source='get_alert_display', read_only=True)
    
    class Meta:
        model = VehicleTagAlert
        fields = [
            'id', 'vehicle_tag', 'vehicle_tag_vtid', 'vehicle_tag_registration_no',
            'latitude', 'longitude', 'person_image', 'alert', 'alert_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Convert image field to absolute URL"""
        representation = super().to_representation(instance)
        if instance.person_image:
            request = self.context.get('request')
            if request:
                representation['person_image'] = request.build_absolute_uri(instance.person_image.url)
            else:
                representation['person_image'] = instance.person_image.url
        return representation


class VehicleTagAlertCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vehicle tag alerts"""
    vtid = serializers.CharField(write_only=True, help_text="Vehicle Tag ID (VTID)")
    latitude = serializers.DecimalField(
        max_digits=18,
        decimal_places=15,
        required=True,
        help_text="Latitude where alert was reported (required)"
    )
    longitude = serializers.DecimalField(
        max_digits=19,
        decimal_places=15,
        required=True,
        help_text="Longitude where alert was reported (required)"
    )
    person_image = serializers.ImageField(
        required=True,
        help_text="Image of person reporting the alert (required)"
    )
    
    class Meta:
        model = VehicleTagAlert
        fields = ['vtid', 'latitude', 'longitude', 'person_image', 'alert']
    
    def create(self, validated_data):
        """Create alert with vtid lookup and cooldown validation"""
        from vehicle_tag.models import VehicleTag
        
        vtid = validated_data.pop('vtid')
        try:
            vehicle_tag = VehicleTag.objects.get(vtid=vtid)
        except VehicleTag.DoesNotExist:
            raise serializers.ValidationError(f"Vehicle tag with VTID {vtid} not found")
        
        # Check for cooldown period (10 minutes)
        latest_alert = VehicleTagAlert.objects.filter(
            vehicle_tag=vehicle_tag
        ).order_by('-created_at').first()
        
        if latest_alert:
            time_since_last_alert = timezone.now() - latest_alert.created_at
            cooldown_period = timedelta(minutes=10)
            
            if time_since_last_alert < cooldown_period:
                remaining_seconds = int((cooldown_period - time_since_last_alert).total_seconds())
                remaining_minutes = remaining_seconds // 60
                remaining_secs = remaining_seconds % 60
                
                raise serializers.ValidationError(
                    f"Please wait before sending another alert. A recent alert was sent less than 10 minutes ago. "
                    f"Please wait {remaining_minutes}:{remaining_secs:02d} more."
                )
        
        validated_data['vehicle_tag'] = vehicle_tag
        return super().create(validated_data)

