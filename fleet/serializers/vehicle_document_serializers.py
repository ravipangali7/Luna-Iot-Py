"""
Vehicle Document Serializers
Handles serialization for vehicle document management endpoints
"""
from rest_framework import serializers
from fleet.models import VehicleDocument, Vehicle


class VehicleDocumentSerializer(serializers.ModelSerializer):
    """Serializer for vehicle document model"""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    
    class Meta:
        model = VehicleDocument
        fields = [
            'id', 'vehicle', 'vehicle_name', 'vehicle_imei', 'title', 
            'last_expire_date', 'expire_in_month', 'document_image_one', 
            'document_image_two', 'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vehicle document records"""
    
    class Meta:
        model = VehicleDocument
        fields = [
            'vehicle', 'title', 'last_expire_date', 'expire_in_month', 
            'document_image_one', 'document_image_two', 'remarks'
        ]
    
    def validate_expire_in_month(self, value):
        """Validate expire in month"""
        if value <= 0:
            raise serializers.ValidationError("Expire in month must be greater than 0")
        return value


class VehicleDocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating vehicle document records"""
    
    class Meta:
        model = VehicleDocument
        fields = [
            'title', 'last_expire_date', 'expire_in_month', 
            'document_image_one', 'document_image_two', 'remarks'
        ]
    
    def validate_expire_in_month(self, value):
        """Validate expire in month"""
        if value <= 0:
            raise serializers.ValidationError("Expire in month must be greater than 0")
        return value


class VehicleDocumentListSerializer(serializers.ModelSerializer):
    """Serializer for vehicle document list (minimal data)"""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    
    class Meta:
        model = VehicleDocument
        fields = [
            'id', 'vehicle_name', 'title', 'last_expire_date', 
            'expire_in_month', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class VehicleDocumentRenewSerializer(serializers.Serializer):
    """Serializer for document renewal"""
    confirm = serializers.BooleanField(help_text="Confirmation to renew document")
    
    def validate_confirm(self, value):
        """Validate confirmation"""
        if not value:
            raise serializers.ValidationError("Must confirm to renew document")
        return value

