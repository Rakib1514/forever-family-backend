from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

class MultiIdentifierBackend(ModelBackend):
    """
    Custom authentication backend that allows authentication with 
    username, email, or phone number.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        try:
            # Check if the username is email, phone_number, or username
            user = User.objects.get(
                Q(username=username) | 
                Q(email=username) | 
                Q(phone_number=username)
            )
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # If multiple users found, use the first one (shouldn't happen with unique constraints)
            user = User.objects.filter(
                Q(username=username) | 
                Q(email=username) | 
                Q(phone_number=username)
            ).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
