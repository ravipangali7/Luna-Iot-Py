"""
Phone Book Number Serializers
Handles serialization for phone book number management endpoints
"""
from rest_framework import serializers
from phone_call.models import PhoneBookNumber, PhoneBook


class PhoneBookNumberSerializer(serializers.ModelSerializer):
    """Serializer for phone book number model (detail view)"""
    phonebook_name = serializers.CharField(source='phonebook.name', read_only=True)
    
    class Meta:
        model = PhoneBookNumber
        fields = [
            'id', 'phonebook', 'phonebook_name', 'name', 'phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PhoneBookNumberCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating phone book numbers"""
    
    class Meta:
        model = PhoneBookNumber
        fields = ['phonebook', 'name', 'phone']
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_phone(self, value):
        """Validate phone"""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone cannot be empty")
        return value.strip()
    
    def validate_phonebook(self, value):
        """Validate phonebook exists"""
        if not value:
            raise serializers.ValidationError("Phone book is required")
        return value
    
    def validate(self, data):
        """Validate phone uniqueness within phone book"""
        phonebook = data.get('phonebook')
        phone = data.get('phone')
        
        if phonebook and phone:
            # Check if phone already exists in this phone book
            existing = PhoneBookNumber.objects.filter(
                phonebook=phonebook,
                phone=phone
            )
            # Exclude current instance if updating
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            
            if existing.exists():
                raise serializers.ValidationError({
                    'phone': 'This phone number already exists in this phone book'
                })
        
        return data


class PhoneBookNumberUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating phone book numbers"""
    
    class Meta:
        model = PhoneBookNumber
        fields = ['name', 'phone']
        extra_kwargs = {
            'name': {'required': False},
            'phone': {'required': False}
        }
    
    def validate_name(self, value):
        """Validate name"""
        if value and not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip() if value else value
    
    def validate_phone(self, value):
        """Validate phone"""
        if value and not value.strip():
            raise serializers.ValidationError("Phone cannot be empty")
        return value.strip() if value else value
    
    def validate(self, data):
        """Validate phone uniqueness within phone book"""
        phone = data.get('phone')
        
        if phone and self.instance:
            # Check if phone already exists in this phone book
            existing = PhoneBookNumber.objects.filter(
                phonebook=self.instance.phonebook,
                phone=phone
            ).exclude(id=self.instance.id)
            
            if existing.exists():
                raise serializers.ValidationError({
                    'phone': 'This phone number already exists in this phone book'
                })
        
        return data


class PhoneBookNumberListSerializer(serializers.ModelSerializer):
    """Serializer for phone book number list (minimal data)"""
    
    class Meta:
        model = PhoneBookNumber
        fields = ['id', 'name', 'phone', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
