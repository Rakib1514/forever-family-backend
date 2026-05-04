from django.urls import path
from .views import RoomListView, GenerateInviteCodeView, JoinRoomByCodeView

urlpatterns = [
    path('', RoomListView.as_view(), name='room-list'),
    path('<int:pk>/generate-invite/', GenerateInviteCodeView.as_view(), name='generate-invite'),
    path('join/', JoinRoomByCodeView.as_view(), name='join-room'),
]
