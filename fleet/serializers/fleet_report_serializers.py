"""
Fleet Report Serializers
Handles serialization for fleet report endpoints
"""
from rest_framework import serializers
from datetime import datetime


class FleetReportSerializer(serializers.Serializer):
    """Serializer for fleet report response"""
    total_days = serializers.IntegerField()
    
    servicing = serializers.DictField()
    expenses = serializers.DictField()
    energy_cost = serializers.DictField()


class FleetReportRequestSerializer(serializers.Serializer):
    """Serializer for fleet report request"""
    from_date = serializers.DateField(required=True)
    to_date = serializers.DateField(required=True)
    
    def validate(self, data):
        """Validate date range"""
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        
        if from_date and to_date:
            if from_date > to_date:
                raise serializers.ValidationError("from_date cannot be greater than to_date")
            
            # Check if date range is not too large (e.g., more than 5 years)
            days_diff = (to_date - from_date).days
            if days_diff > 1825:  # 5 years
                raise serializers.ValidationError("Date range cannot exceed 5 years")
        
        return data

