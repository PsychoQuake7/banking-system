from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Notification
from .services import NotificationService
from users.models import CustomUser

@login_required
def notification_list_view(request):
    """
    Display user's notifications with filtering options.
    """
    # Get user's notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-sent_date')
    
    # Apply filters
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    status = request.GET.get('status')
    if status:
        notifications = notifications.filter(status=status)
    
    start_date = request.GET.get('start_date')
    if start_date:
        notifications = notifications.filter(sent_date__gte=start_date)
    
    end_date = request.GET.get('end_date')
    if end_date:
        notifications = notifications.filter(sent_date__lte=end_date)
    
    # Get all users for admin notification sending
    all_users = None
    if request.user.role in ['admin', 'staff']:
        all_users = CustomUser.objects.filter(is_active=True).order_by('username')
    
    context = {
        'notifications': notifications,
        'all_users': all_users,
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
def send_notification_view(request):
    """
    Handle sending notifications (admin/staff only).
    """
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, "You do not have permission to send notifications.")
        return redirect('notifications:notification_list')
    
    # Get all users for selection
    all_users = CustomUser.objects.filter(is_active=True).order_by('username')
    
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        notification_type = request.POST.get('notification_type')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if not all([recipient_id, notification_type, subject, message]):
            messages.error(request, "All fields are required.")
            return render(request, 'notifications/send_notification.html', {
                'all_users': all_users
            })
        
        try:
            recipient = CustomUser.objects.get(user_id=recipient_id)
            
            NotificationService.send_notification(
                user=recipient,
                subject=subject,
                message=message,
                notification_type=notification_type,
                related_entity_type='system',
                related_entity_id=0
            )
            messages.success(request, f"Notification sent successfully to {recipient.username} ({recipient.email}).")
            return redirect('notifications:notification_list')
        except CustomUser.DoesNotExist:
            messages.error(request, "Selected user not found.")
        except Exception as e:
            messages.error(request, f"Failed to send notification: {str(e)}")
    
    # GET request - show form
    context = {
        'all_users': all_users,
    }
    return render(request, 'notifications/send_notification.html', context)

@login_required
def notification_settings_view(request):
    return render(request, 'notifications/notification_settings.html')