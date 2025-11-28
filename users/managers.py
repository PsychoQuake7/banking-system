from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Custom user manager for CustomUser model.
    Handles user and superuser creation with role assignment.
    """
    
    def create_user(self, username, email=None, password=None, role='borrower', **extra_fields):
        """
        Create and save a regular user with the given username, email, password, and role.
        """
        if not username:
            raise ValueError('The Username field must be set')
        
        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Create and save a superuser with the given username, email, and password.
        Superusers are automatically assigned the 'admin' role.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')  # Superusers are always admins
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)
