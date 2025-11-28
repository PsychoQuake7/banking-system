from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Custom admin interface for CustomUser model.
    Adds role field to the admin interface.
    """
    
    # Fields to display in the user list
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active']
    
    # Filters for the sidebar
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active', 'groups']
    
    # Search fields
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    # Ordering
    ordering = ['username']
    
    # Fieldsets for the user detail/edit page
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fieldsets for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
