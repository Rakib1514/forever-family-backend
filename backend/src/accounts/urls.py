from django.urls import path
from .views import (
    RegisterView, UserProfileView, LogoutView, 
    ShadowUserCreateView, UserDetailView, UserListView,
    ShadowUserUpdateView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('shadow-user/', ShadowUserCreateView.as_view(), name='shadow-user-create'),
    path('shadow-user/<int:id>/', ShadowUserUpdateView.as_view(), name='shadow-user-update'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/<int:id>/', UserDetailView.as_view(), name='user-detail'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
