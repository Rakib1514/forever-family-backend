from rest_framework import generics, permissions
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
