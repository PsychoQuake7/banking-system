from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """
    Custom User model with role field for access control.
    Extends Django's AbstractUser to add role-based permissions.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('borrower', 'Borrower'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='borrower',
        help_text='User role for access control'
    )
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def is_staff_member(self):
        """Check if user has staff role"""
        return self.role == 'staff'
    
    def is_borrower(self):
        """Check if user has borrower role"""
        return self.role == 'borrower'
