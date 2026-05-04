import random
import string
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Room
from .serializers import RoomSerializer

@extend_schema_view(
    get=extend_schema(tags=['Room'])
)
class RoomListView(generics.ListAPIView):
    """
    Returns a list of rooms owned by the user or where the user is a member.
    """
    serializer_class = RoomSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        # Return rooms where user is owner OR a member
        return Room.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().order_by('-created_at')

class GenerateInviteCodeView(APIView):
    """Generate a unique 6-character invite code for a room owned by the user."""
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(tags=['Room'])
    def post(self, request, pk):
        try:
            room = Room.objects.get(pk=pk, owner=request.user)
        except Room.DoesNotExist:
            return Response({"error": "Room not found or you are not the owner."}, status=status.HTTP_404_NOT_FOUND)

        # Generate unique 6-char code
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(6))
            if not Room.objects.filter(invite_code=code).exists():
                break
        
        room.invite_code = code
        room.save()
        return Response({"invite_code": code}, status=status.HTTP_200_OK)

from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer

class JoinRoomByCodeView(APIView):
    """Join a room using a 6-character invite code."""
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        tags=['Room'],
        request=inline_serializer(
            name='JoinRoomRequest',
            fields={
                'code': serializers.CharField(max_length=6)
            }
        )
    )
    def post(self, request):
        code = request.data.get('code', '').upper()
        if not code:
            return Response({"error": "Code is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            room = Room.objects.get(invite_code=code)
        except Room.DoesNotExist:
            return Response({"error": "Invalid invite code."}, status=status.HTTP_404_NOT_FOUND)

        if room.members.filter(id=request.user.id).exists() or room.owner == request.user:
            return Response({"message": "You are already a member of this room."}, status=status.HTTP_200_OK)

        room.members.add(request.user)
        return Response({"message": f"Successfully joined room: {room.name}"}, status=status.HTTP_200_OK)
