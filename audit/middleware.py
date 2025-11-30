from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog
from .utils import get_client_ip
import json

class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log user actions.
    Logs POST, PUT, PATCH, DELETE requests with user, IP, action, and details.
    """
    
    # Paths to skip logging (static files, media, etc.)
    SKIP_PATHS = [
        '/static/',
        '/media/',
        '/admin/jsi18n/',
        '/__debug__/',
    ]
    
    # Methods to log
    LOG_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    def process_response(self, request, response):
        """
        Log the request after processing.
        """
        # Skip if not a logged method
        if request.method not in self.LOG_METHODS:
            return response
        
        # Skip static/media paths
        if any(request.path.startswith(skip) for skip in self.SKIP_PATHS):
            return response
        
        # Skip if user is not authenticated (optional: you can log anonymous too)
        if not request.user.is_authenticated:
            return response
        
        # Extract details
        action = f"{request.method} {request.path}"
        ip_address = get_client_ip(request)
        
        # Build details from POST data (be careful with sensitive data)
        details = self._build_details(request)
        
        # Create audit log
        try:
            AuditLog.objects.create(
                user=request.user,
                action=action,
                ip_address=ip_address,
                details=details
            )
        except Exception as e:
            # Don't break the request if logging fails
            print(f"Audit logging failed: {e}")
        
        return response
    
    def _build_details(self, request):
        """
        Build details string from request data.
        Excludes sensitive fields like passwords.
        """
        try:
            # Get POST data
            data = request.POST.copy()
            
            # Remove sensitive fields
            sensitive_fields = ['password', 'password1', 'password2', 'csrfmiddlewaretoken']
            for field in sensitive_fields:
                if field in data:
                    data[field] = '***REDACTED***'
            
            # Convert to JSON string
            if data:
                return json.dumps(dict(data), indent=2)
            
            # If no POST data, try to get a summary from the path
            return f"Request to {request.path}"
        except Exception:
            return "Unable to capture details"
