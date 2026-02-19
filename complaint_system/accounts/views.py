"""
Views for user authentication and registration.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .forms import (
    StudentRegistrationForm,
    StudentLoginForm,
    StaffLoginForm,
    AdminLoginForm
)
from .models import CustomUser


@csrf_protect
@require_http_methods(["GET", "POST"])
def student_register(request):
    """Handle student registration."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('complaints:student_create_complaint')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'accounts/student_register.html', {'form': form})


@csrf_protect
@require_http_methods(["GET", "POST"])
def student_login(request):
    """Handle student login."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    
    if request.method == 'POST':
        form = StudentLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.GET.get('next', 'complaints:student_my_complaints')
            return redirect(next_url)
    else:
        form = StudentLoginForm()
    
    return render(request, 'accounts/student_login.html', {'form': form})


@csrf_protect
@require_http_methods(["GET", "POST"])
def staff_login(request):
    """Handle staff login."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    
    if request.method == 'POST':
        form = StaffLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.GET.get('next', 'complaints:staff_assigned_complaints')
            return redirect(next_url)
    else:
        form = StaffLoginForm()
    
    return render(request, 'accounts/staff_login.html', {'form': form})


@csrf_protect
@require_http_methods(["GET", "POST"])
def admin_login(request):
    """Handle admin login."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    
    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.GET.get('next', 'complaints:admin_dashboard')
            return redirect(next_url)
    else:
        form = AdminLoginForm()
    
    return render(request, 'accounts/admin_login.html', {'form': form})


@login_required
def dashboard_redirect(request):
    """Redirect user to appropriate dashboard based on role."""
    user = request.user
    
    if user.is_student:
        return redirect('complaints:student_my_complaints')
    elif user.is_staff_member:
        return redirect('complaints:staff_assigned_complaints')
    elif user.is_admin_user:
        return redirect('complaints:admin_dashboard')
    else:
        messages.error(request, 'Invalid user role. Please contact administrator.')
        return redirect('home')


@login_required
def user_logout(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')
