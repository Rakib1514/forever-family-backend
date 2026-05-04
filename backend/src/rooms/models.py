from django.db import models
from django.conf import settings

class Room(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='owned_rooms'
    )
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='managed_rooms',
        blank=True
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='accessible_rooms',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
