"""
School Parents Serializers
Handles serialization for school parent management endpoints
"""
from rest_framework import serializers
from school.models import SchoolParent, SchoolBus
from core.serializers import UserSerializer


class SchoolParentSerializer(serializers.ModelSerializer):
    """Serializer for school parent model"""
    parent = UserSerializer(read_only=True)
    parent_id = serializers.IntegerField(write_only=True, required=False)
    school_buses = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=SchoolBus.objects.all(),
        required=False
    )
    
    class Meta:
        model = SchoolParent
        fields = [
            'id', 'parent', 'parent_id', 'school_buses', 'latitude', 'longitude',
            'child_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SchoolParentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating school parents"""
    school_buses = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=SchoolBus.objects.all(),
        required=False
    )
    
    class Meta:
        model = SchoolParent
        fields = ['parent', 'school_buses', 'latitude', 'longitude', 'child_name']
    
    def create(self, validated_data):
        """Create school parent with bus assignments"""
        school_buses = validated_data.pop('school_buses', [])
        school_parent = SchoolParent.objects.create(**validated_data)
        if school_buses:
            school_parent.school_buses.set(school_buses)
        return school_parent
    
    def update(self, instance, validated_data):
        """Update school parent and bus assignments"""
        school_buses = validated_data.pop('school_buses', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if school_buses is not None:
            instance.school_buses.set(school_buses)
        
        return instance


class SchoolParentListSerializer(serializers.ModelSerializer):
    """Serializer for school parent list (minimal data)"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    parent_phone = serializers.CharField(source='parent.phone', read_only=True)
    school_buses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SchoolParent
        fields = [
            'id', 'parent_name', 'parent_phone', 'school_buses_count',
            'latitude', 'longitude', 'child_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_school_buses_count(self, obj):
        return obj.school_buses.count()

