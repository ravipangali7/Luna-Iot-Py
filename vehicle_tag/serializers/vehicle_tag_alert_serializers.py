"""
Vehicle Tag Alert Serializers
Handles serialization for vehicle tag alert endpoints
"""
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
    
    class Meta:
        model = VehicleTagAlert
        fields = ['vtid', 'latitude', 'longitude', 'person_image', 'alert']
    
    def create(self, validated_data):
        """Create alert with vtid lookup"""
        from vehicle_tag.models import VehicleTag
        
        vtid = validated_data.pop('vtid')
        try:
            vehicle_tag = VehicleTag.objects.get(vtid=vtid)
        except VehicleTag.DoesNotExist:
            raise serializers.ValidationError(f"Vehicle tag with VTID {vtid} not found")
        
        validated_data['vehicle_tag'] = vehicle_tag
        return super().create(validated_data)

