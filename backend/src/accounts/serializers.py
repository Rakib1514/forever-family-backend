from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Lightweight serializer for nested user info."""
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'nick_name', 'gender')

class UserSerializer(serializers.ModelSerializer):
    mother_detail = UserBasicSerializer(source='mother', read_only=True)
    father_detail = UserBasicSerializer(source='father', read_only=True)
    spouse_detail = UserBasicSerializer(source='spouse', read_only=True)
    children = UserBasicSerializer(many=True, read_only=True)
    brothers = UserBasicSerializer(many=True, read_only=True)
    sisters = UserBasicSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'phone_number', 'first_name', 'last_name', 'nick_name', 
            'birth_date', 'passed_on', 'gender', 'current_address', 
            'permanent_address', 'is_primary', 
            'mother', 'mother_detail', 
            'father', 'father_detail', 
            'spouse', 'spouse_detail',
            'brothers', 'sisters',
            'children'
        )
        read_only_fields = ('id',)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_null=True)
    username = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'first_name', 'last_name', 'phone_number')

    def validate(self, attrs):
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')

        if not email and not phone_number:
            raise serializers.ValidationError("Either email or phone number must be provided.")
        return attrs

    def create(self, validated_data):
        # Force is_primary to True for sign-ups
        validated_data['is_primary'] = True
        # UserManager.create_user already handles auto-username if not provided
        return User.objects.create_user(**validated_data)

class ShadowUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'email', 'phone_number', 
            'nick_name', 'birth_date', 'gender'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        # Create user without password and is_primary=False
        validated_data['is_primary'] = False
        # UserManager.create_user handles username generation
        user = User.objects.create_user(**validated_data)
        user.set_unusable_password()
        user.save()
        return user
