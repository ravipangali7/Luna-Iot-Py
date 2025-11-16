"""
Banner Serializers
Handles serialization for banner management endpoints
"""
from rest_framework import serializers
from shared.models import Banner


class BannerSerializer(serializers.ModelSerializer):
    """Serializer for banner model"""
    
    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'image', 'url', 
            'is_active', 'click', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'click', 'created_at', 'updated_at']


class BannerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating banners"""
    
    class Meta:
        model = Banner
        fields = ['title', 'image', 'url', 'is_active']
    
    def validate_title(self, value):
        """Validate banner title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Banner title cannot be empty")
        return value.strip()
    
    def validate_url(self, value):
        """Validate banner URL"""
        if not value or not value.strip():
            raise serializers.ValidationError("Banner URL cannot be empty")
        return value.strip()


class BannerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating banners"""
    
    class Meta:
        model = Banner
        fields = ['title', 'image', 'url', 'is_active']
    
    def validate_title(self, value):
        """Validate banner title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Banner title cannot be empty")
        return value.strip()
    
    def validate_url(self, value):
        """Validate banner URL"""
        if not value or not value.strip():
            raise serializers.ValidationError("Banner URL cannot be empty")
        return value.strip()


class BannerListSerializer(serializers.ModelSerializer):
    """Serializer for banner list (minimal data)"""
    
    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'is_active', 'click', 'created_at'
        ]
        read_only_fields = ['id', 'click', 'created_at']


class ActiveBannerSerializer(serializers.ModelSerializer):
    """Serializer for active banners"""
    
    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'image', 'url', 'click', 'created_at'
        ]
        read_only_fields = ['id', 'click', 'created_at']


class BannerStatsSerializer(serializers.Serializer):
    """Serializer for banner statistics"""
    total_banners = serializers.IntegerField()
    active_banners = serializers.IntegerField()
    inactive_banners = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    recent_banners = serializers.IntegerField()

