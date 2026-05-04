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
    
    # New Fields
    full_name = serializers.CharField(write_only=True, required=True)
    nick_name = serializers.CharField(required=True)
    birth_date = serializers.DateField(required=True)
    father_name = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    mother_name = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    force_create = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'password', 'full_name', 'nick_name', 
            'phone_number', 'birth_date', 'father_name', 'mother_name', 'force_create'
        )

    def validate(self, attrs):
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')

        if not email and not phone_number:
            raise serializers.ValidationError({"error": "Either email or phone number must be provided."})
            
        force_create = attrs.get('force_create', False)
        
        if not force_create:
            from .utils import check_duplicate_user
            
            # For simplicity in fuzzy matching, we pass the full_name as first_name
            decision = check_duplicate_user(
                birth_date=attrs.get('birth_date'),
                first_name=attrs.get('full_name'),
                last_name='',
                nick_name=attrs.get('nick_name'),
                father_name=attrs.get('father_name'),
                mother_name=attrs.get('mother_name')
            )
            
            if decision in ["POSSIBLE_DUPLICATE", "VERY_LIKELY_DUPLICATE"]:
                raise serializers.ValidationError({
                    "decision": decision,
                    "message": f"Account creation paused. Status: {decision}. Send 'force_create': true to bypass."
                })

        return attrs

    def create(self, validated_data):
        # Remove non-model fields
        validated_data.pop('father_name', None)
        validated_data.pop('mother_name', None)
        validated_data.pop('force_create', None)
        
        # Handle full_name
        full_name = validated_data.pop('full_name', '')
        name_parts = full_name.split(' ', 1)
        validated_data['first_name'] = name_parts[0]
        if len(name_parts) > 1:
            validated_data['last_name'] = name_parts[1]

        # Force is_primary to True for sign-ups
        validated_data['is_primary'] = True
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
