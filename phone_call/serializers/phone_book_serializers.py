"""
Phone Book Serializers
Handles serialization for phone book management endpoints
"""
from rest_framework import serializers
from phone_call.models import PhoneBook, PhoneBookNumber
from core.models import User, Institute


class PhoneBookNumberListSerializer(serializers.ModelSerializer):
    """Serializer for phone book numbers in list view"""
    
    class Meta:
        model = PhoneBookNumber
        fields = ['id', 'name', 'phone', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PhoneBookSerializer(serializers.ModelSerializer):
    """Serializer for phone book model (detail view with nested numbers)"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    numbers = PhoneBookNumberListSerializer(many=True, read_only=True)
    numbers_count = serializers.SerializerMethodField()
    owner_type = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PhoneBook
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'institute', 'institute_name',
            'name', 'numbers', 'numbers_count', 'owner_type', 'owner_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'numbers_count']
    
    def get_numbers_count(self, obj):
        """Get number of contacts in phone book"""
        return obj.numbers.count()
    
    def get_owner_type(self, obj):
        """Get owner type (user or institute)"""
        return 'user' if obj.user else 'institute'
    
    def get_owner_name(self, obj):
        """Get owner name"""
        if obj.user:
            return obj.user.name or obj.user.phone
        elif obj.institute:
            return obj.institute.name
        return None


class PhoneBookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating phone books"""
    
    class Meta:
        model = PhoneBook
        fields = ['name', 'user', 'institute']
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate(self, data):
        """Validate that exactly one of user or institute is provided"""
        user = data.get('user')
        institute = data.get('institute')
        
        if not user and not institute:
            raise serializers.ValidationError("Either user or institute must be provided")
        if user and institute:
            raise serializers.ValidationError("Phone book cannot belong to both user and institute")
        
        # Validate user exists if provided
        if user:
            try:
                User.objects.get(id=user.id if hasattr(user, 'id') else user)
            except User.DoesNotExist:
                raise serializers.ValidationError("User does not exist")
        
        # Validate institute exists if provided
        if institute:
            try:
                Institute.objects.get(id=institute.id if hasattr(institute, 'id') else institute)
            except Institute.DoesNotExist:
                raise serializers.ValidationError("Institute does not exist")
        
        return data


class PhoneBookUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating phone books"""
    
    class Meta:
        model = PhoneBook
        fields = ['name']
        extra_kwargs = {
            'name': {'required': False}
        }
    
    def validate_name(self, value):
        """Validate name"""
        if value and not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip() if value else value


class PhoneBookListSerializer(serializers.ModelSerializer):
    """Serializer for phone book list (minimal data)"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    numbers_count = serializers.SerializerMethodField()
    owner_type = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PhoneBook
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'institute', 'institute_name',
            'name', 'numbers_count', 'owner_type', 'owner_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_numbers_count(self, obj):
        """Get number of contacts in phone book"""
        return obj.numbers.count()
    
    def get_owner_type(self, obj):
        """Get owner type (user or institute)"""
        return 'user' if obj.user else 'institute'
    
    def get_owner_name(self, obj):
        """Get owner name"""
        if obj.user:
            return obj.user.name or obj.user.phone
        elif obj.institute:
            return obj.institute.name
        return None
