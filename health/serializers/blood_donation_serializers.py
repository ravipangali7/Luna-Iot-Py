"""
Blood Donation Serializers
Handles serialization for blood donation management endpoints
"""
from rest_framework import serializers
from health.models import BloodDonation
from api_common.utils.validation_utils import validate_phone_number


class BloodDonationSerializer(serializers.ModelSerializer):
    """Serializer for blood donation model"""
    
    class Meta:
        model = BloodDonation
        fields = [
            'id', 'name', 'phone', 'address', 'blood_group', 
            'apply_type', 'status', 'last_donated_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BloodDonationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating blood donation records"""
    
    class Meta:
        model = BloodDonation
        fields = [
            'name', 'phone', 'address', 'blood_group', 
            'apply_type', 'last_donated_at'
        ]
    
    def validate_name(self, value):
        """Validate donor name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Donor name cannot be empty")
        return value.strip()
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()
    
    def validate_address(self, value):
        """Validate address"""
        if not value or not value.strip():
            raise serializers.ValidationError("Address cannot be empty")
        return value.strip()
    
    def validate_blood_group(self, value):
        """Validate blood group"""
        valid_blood_groups = [
            'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'
        ]
        if value not in valid_blood_groups:
            raise serializers.ValidationError(
                f"Invalid blood group. Must be one of: {', '.join(valid_blood_groups)}"
            )
        return value
    
    def validate_apply_type(self, value):
        """Validate apply type"""
        valid_types = ['DONOR', 'RECIPIENT']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid apply type. Must be one of: {', '.join(valid_types)}"
            )
        return value


class BloodDonationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating blood donation records"""
    
    class Meta:
        model = BloodDonation
        fields = [
            'name', 'phone', 'address', 'blood_group', 
            'apply_type', 'status', 'last_donated_at'
        ]
    
    def validate_name(self, value):
        """Validate donor name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Donor name cannot be empty")
        return value.strip()
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()
    
    def validate_address(self, value):
        """Validate address"""
        if not value or not value.strip():
            raise serializers.ValidationError("Address cannot be empty")
        return value.strip()
    
    def validate_blood_group(self, value):
        """Validate blood group"""
        valid_blood_groups = [
            'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'
        ]
        if value not in valid_blood_groups:
            raise serializers.ValidationError(
                f"Invalid blood group. Must be one of: {', '.join(valid_blood_groups)}"
            )
        return value
    
    def validate_apply_type(self, value):
        """Validate apply type"""
        valid_types = ['DONOR', 'RECIPIENT']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid apply type. Must be one of: {', '.join(valid_types)}"
            )
        return value


class BloodDonationListSerializer(serializers.ModelSerializer):
    """Serializer for blood donation list (minimal data)"""
    
    class Meta:
        model = BloodDonation
        fields = [
            'id', 'name', 'phone', 'blood_group', 
            'apply_type', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BloodDonationFilterSerializer(serializers.Serializer):
    """Serializer for blood donation search filters"""
    name = serializers.CharField(
        required=False,
        help_text="Filter by donor name"
    )
    phone = serializers.CharField(
        required=False,
        help_text="Filter by phone number"
    )
    blood_group = serializers.CharField(
        required=False,
        help_text="Filter by blood group"
    )
    apply_type = serializers.CharField(
        required=False,
        help_text="Filter by apply type"
    )
    status = serializers.BooleanField(
        required=False,
        help_text="Filter by status"
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Start date for filtering"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="End date for filtering"
    )
    
    def validate_phone(self, value):
        """Validate phone number format if provided"""
        if value and not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value
    
    def validate_blood_group(self, value):
        """Validate blood group if provided"""
        if value:
            valid_blood_groups = [
                'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'
            ]
            if value not in valid_blood_groups:
                raise serializers.ValidationError(
                    f"Invalid blood group. Must be one of: {', '.join(valid_blood_groups)}"
                )
        return value
    
    def validate_apply_type(self, value):
        """Validate apply type if provided"""
        if value:
            valid_types = ['DONOR', 'RECIPIENT']
            if value not in valid_types:
                raise serializers.ValidationError(
                    f"Invalid apply type. Must be one of: {', '.join(valid_types)}"
                )
        return value
    
    def validate(self, data):
        """Validate date range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        return data


class BloodDonationStatsSerializer(serializers.Serializer):
    """Serializer for blood donation statistics"""
    total_donations = serializers.IntegerField()
    donors = serializers.IntegerField()
    recipients = serializers.IntegerField()
    active_donations = serializers.IntegerField()
    inactive_donations = serializers.IntegerField()
    donations_by_blood_group = serializers.DictField()
    donations_by_type = serializers.DictField()
    recent_donations = serializers.IntegerField()


class BloodDonationByTypeSerializer(serializers.Serializer):
    """Serializer for blood donations by type"""
    apply_type = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class BloodDonationByBloodGroupSerializer(serializers.Serializer):
    """Serializer for blood donations by blood group"""
    blood_group = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class BloodDonationStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating blood donation status"""
    status = serializers.BooleanField(
        help_text="New status for the blood donation record"
    )
    
    def validate_status(self, value):
        """Validate status value"""
        if not isinstance(value, bool):
            raise serializers.ValidationError("Status must be a boolean value")
        return value
