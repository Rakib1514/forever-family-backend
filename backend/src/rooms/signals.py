from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Room

User = get_user_model()

@receiver(post_save, sender=User)
def create_default_room(sender, instance, created, **kwargs):
    """
    Automatically create a default room for newly registered primary users.
    """
    if created and instance.is_primary:
        room_name = f"{instance.first_name or instance.username}'s Family Room"
        room = Room.objects.create(name=room_name, owner=instance)
        room.members.add(instance)
