from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from .serializers import (
    UserSerializer, RegisterSerializer, ShadowUserSerializer,
    UserListSerializer
)
from rooms.models import Room

User = get_user_model()

@extend_schema_view(
    post=extend_schema(tags=['Authentication'])
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

@extend_schema_view(
    get=extend_schema(tags=['Authentication']),
    patch=extend_schema(tags=['Authentication'])
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user

@extend_schema_view(
    post=extend_schema(tags=['Authentication'])
)
class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    post=extend_schema(tags=['Member'])
)
class ShadowUserCreateView(generics.CreateAPIView):
    """
    Creates a shadow user (non-primary, no password) and adds them 
    to a room owned by the creator.
    """
    serializer_class = ShadowUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        # Create the shadow user
        shadow_user = serializer.save()
        
        # Find a room owned by the creator
        # For now, we take the first room they own
        room = Room.objects.filter(owner=self.request.user).first()
        if room:
            room.members.add(shadow_user)

from django.core.cache import cache

class SharedUserVisibilityMixin:
    """Mixin to provide queryset for users sharing a room with the requester."""
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
            
        cache_key = f"user_list_{user.id}"
        cached_qs = cache.get(cache_key)
        if cached_qs is not None:
            return cached_qs
            
        # 1. Get IDs of all rooms the requester is involved in
        room_ids = Room.objects.filter(
            Q(owner=user) | Q(members=user) | Q(admins=user)
        ).values_list('id', flat=True)
        
        # 2. Get all users associated with those specific rooms
        qs = User.objects.filter(
            Q(id=user.id) |
            Q(owned_rooms__id__in=room_ids) |
            Q(accessible_rooms__id__in=room_ids) |
            Q(managed_rooms__id__in=room_ids)
        ).distinct().order_by('first_name', 'last_name')
        
        # Cache for 5 minutes
        cache.set(cache_key, qs, 300)
        return qs

@extend_schema_view(
    get=extend_schema(tags=['Member'])
)
class UserListView(SharedUserVisibilityMixin, generics.ListAPIView):
    """List all users shared across rooms. Uses a lightweight serializer for performance."""
    serializer_class = UserListSerializer
    permission_classes = (permissions.IsAuthenticated,)

@extend_schema_view(
    get=extend_schema(tags=['Authentication'])
)
class UserDetailView(SharedUserVisibilityMixin, generics.RetrieveAPIView):
    """
    Retrieve user profile by ID. 
    Visible only if it's the requester's own account or they share a room.
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'id'

@extend_schema_view(
    patch=extend_schema(tags=['Member'])
)
class ShadowUserUpdateView(generics.UpdateAPIView):
    """
    Update a shadow user profile. 
    Allowed for any member/admin of the room they belong to.
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ['patch']
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        # Rooms requester is in
        accessible_rooms = Room.objects.filter(
            Q(owner=user) | Q(members=user) | Q(admins=user)
        )
        # Return only shadow users (is_primary=False) who are in those rooms
        return User.objects.filter(
            is_primary=False,
            accessible_rooms__in=accessible_rooms
        ).distinct()

