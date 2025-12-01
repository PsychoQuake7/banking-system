
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import AdminUserCreationForm

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

@login_required
@user_passes_test(is_admin)
def admin_create_user(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully with role {user.get_role_display()}.')
            return redirect('admin_create_user')
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'users/admin_create_user.html', {'form': form})
