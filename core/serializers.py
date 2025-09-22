from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    firstname = serializers.CharField(source='first_name', required=False)
    lastname = serializers.CharField(source='last_name', required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'password', 'firstname', 'lastname',
            'role', 'department', 'blockchain_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        
        user = CustomUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                    return data
                raise serializers.ValidationError('User account is disabled.')
            raise serializers.ValidationError('Invalid credentials.')
        raise serializers.ValidationError('Must include username and password.')

class UserSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'firstname', 'lastname',
            'role', 'department', 'blockchain_address', 'created_at', 'updated_at'
        ]

class UserUpdateSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name', required=False)
    lastname = serializers.CharField(source='last_name', required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'firstname', 'lastname',
            'role', 'department', 'blockchain_address'
        ]