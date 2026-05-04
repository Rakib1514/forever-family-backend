from rest_framework import serializers
from .models import Room
from accounts.serializers import UserSerializer

class RoomSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    # We use PrimaryKeyRelatedField for admins/members to keep the list lightweight
    # or nested if preferred. I'll use IDs for now.
    admins_count = serializers.IntegerField(source='admins.count', read_only=True)
    members_count = serializers.IntegerField(source='members.count', read_only=True)

    class Meta:
        model = Room
        fields = (
            'id', 'name', 'owner', 'admins_count', 'members_count', 
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')
