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
        parent = validated_data.get('parent')
        child_name = validated_data.get('child_name')
        
        # Normalize child_name (treat empty/null as same value)
        child_name_normalized = (child_name or '').strip().lower() if child_name else ''
        
        # Check for duplicate: same parent + same bus + same child_name combination
        if school_buses and parent:
            # Check each bus individually
            for bus in school_buses:
                # Find existing SchoolParent records with same parent
                existing_parents = SchoolParent.objects.filter(parent=parent).prefetch_related('school_buses')
                
                for existing_parent in existing_parents:
                    # Check if this bus is already assigned to this parent
                    if existing_parent.school_buses.filter(id=bus.id).exists():
                        # Get the child_name from existing parent and normalize it
                        existing_child_name = (existing_parent.child_name or '').strip().lower() if existing_parent.child_name else ''
                        
                        # Check if child_name matches (both empty/null or both same value)
                        if child_name_normalized == existing_child_name:
                            bus_name = f"{bus.bus.name} ({bus.bus.vehicleNo})" if bus.bus else f"Bus ID {bus.id}"
                            child_display = child_name if child_name else "no child name"
                            raise serializers.ValidationError(
                                f"This parent is already associated with bus '{bus_name}' "
                                f"with the same child name '{child_display}'. "
                                f"Please use a different child name or select a different bus."
                            )
        
        school_parent = SchoolParent.objects.create(**validated_data)
        if school_buses:
            school_parent.school_buses.set(school_buses)
        return school_parent
    
    def update(self, instance, validated_data):
        """Update school parent and bus assignments"""
        school_buses = validated_data.pop('school_buses', None)
        parent = validated_data.get('parent', instance.parent)
        child_name = validated_data.get('child_name', instance.child_name)
        
        # Normalize child_name (treat empty/null as same value)
        child_name_normalized = (child_name or '').strip().lower() if child_name else ''
        
        # Check for duplicate: same parent + same bus + same child_name combination
        # Only check if buses or child_name are being updated
        buses_to_check = school_buses if school_buses is not None else list(instance.school_buses.all())
        
        if buses_to_check and parent:
            # Check each bus individually
            for bus in buses_to_check:
                # Find existing SchoolParent records with same parent, excluding current instance
                existing_parents = SchoolParent.objects.filter(parent=parent).exclude(id=instance.id).prefetch_related('school_buses')
                
                for existing_parent in existing_parents:
                    # Check if this bus is already assigned to this parent
                    if existing_parent.school_buses.filter(id=bus.id).exists():
                        # Get the child_name from existing parent and normalize it
                        existing_child_name = (existing_parent.child_name or '').strip().lower() if existing_parent.child_name else ''
                        
                        # Check if child_name matches (both empty/null or both same value)
                        if child_name_normalized == existing_child_name:
                            bus_name = f"{bus.bus.name} ({bus.bus.vehicleNo})" if bus.bus else f"Bus ID {bus.id}"
                            child_display = child_name if child_name else "no child name"
                            raise serializers.ValidationError(
                                f"This parent is already associated with bus '{bus_name}' "
                                f"with the same child name '{child_display}'. "
                                f"Please use a different child name or select a different bus."
                            )
        
        # Update fields
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

