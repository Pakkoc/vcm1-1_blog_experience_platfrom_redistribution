"""
Admin configuration for users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AdvertiserProfile, InfluencerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for User model"""

    list_display = ['email', 'name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['email', 'name', 'contact']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'contact', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'contact', 'role', 'password1', 'password2'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(AdvertiserProfile)
class AdvertiserProfileAdmin(admin.ModelAdmin):
    """Admin for AdvertiserProfile model"""

    list_display = ['user', 'company_name', 'business_registration_number', 'created_at']
    search_fields = ['company_name', 'business_registration_number', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(InfluencerProfile)
class InfluencerProfileAdmin(admin.ModelAdmin):
    """Admin for InfluencerProfile model"""

    list_display = ['user', 'birth_date', 'sns_link', 'created_at']
    search_fields = ['user__email', 'user__name', 'sns_link']
    readonly_fields = ['created_at', 'updated_at']
