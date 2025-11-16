"""
User models for authentication and profile management.
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Custom user manager"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'advertiser')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model"""

    ROLE_CHOICES = [
        ('advertiser', 'Advertiser'),
        ('influencer', 'Influencer'),
    ]

    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'contact', 'role']

    class Meta:
        db_table = 'users'
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email


class AdvertiserProfile(models.Model):
    """Advertiser profile with company information"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='advertiser_profile',
        primary_key=True
    )
    company_name = models.CharField(max_length=200)
    business_registration_number = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'advertiser_profiles'
        verbose_name = 'advertiser profile'
        verbose_name_plural = 'advertiser profiles'

    def __str__(self):
        return self.company_name


class InfluencerProfile(models.Model):
    """Influencer profile with social media information"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='influencer_profile',
        primary_key=True
    )
    birth_date = models.DateField()
    sns_link = models.URLField(max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'influencer_profiles'
        verbose_name = 'influencer profile'
        verbose_name_plural = 'influencer profiles'

    def __str__(self):
        return self.user.name
