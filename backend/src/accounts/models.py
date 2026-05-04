from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email=None, phone_number=None, username=None, password=None, **extra_fields):
        """Create and save a User with email or phone, auto-generating username if needed."""
        
        if not username:
            import uuid
            username = f"user_{uuid.uuid4().hex[:10]}"
            # Ensure unique username
            while self.model.objects.filter(username=username).exists():
                username = f"user_{uuid.uuid4().hex[:10]}"

        if email:
            email = self.normalize_email(email)
            
        user = self.model(
            email=email, 
            phone_number=phone_number, 
            username=username, 
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, phone_number=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, phone_number, username, password, **extra_fields)

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email=email, username=username, password=password, **extra_fields)

class User(AbstractUser):
    """Custom User model for multi-identifier authentication."""
    
    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    # Custom Fields
    nick_name = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    passed_on = models.DateField(null=True, blank=True, verbose_name="Date of Death")
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    
    current_address = models.TextField(blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    
    is_primary = models.BooleanField(default=False)
    
    # Relationships
    mother = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='children_of_mother'
    )
    father = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='children_of_father'
    )
    spouse = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='spouses'
    )


    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return self.username or self.email or "Unnamed User"

    @property
    def children(self):
        """Helper property to get all children (from either parent)."""
        return User.objects.filter(models.Q(mother=self) | models.Q(father=self))
    
    @property
    def siblings(self):
        """Helper to get all siblings sharing at least one parent."""
        if not self.mother and not self.father:
            return User.objects.none()
        
        q = models.Q()
        if self.mother:
            q |= models.Q(mother=self.mother)
        if self.father:
            q |= models.Q(father=self.father)
            
        return User.objects.filter(q).exclude(id=self.id)
    
    @property
    def brothers(self):
        return self.siblings.filter(gender='M')
    
    @property
    def sisters(self):
        return self.siblings.filter(gender='F')
