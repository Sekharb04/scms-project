"""
Views for the complaints app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.utils import timezone
from functools import wraps

from .models import Complaint, Escalation, Category
from .forms import (
    ComplaintForm, 
    ComplaintStatusUpdateForm, 
    ComplaintCommentForm,
    ComplaintFilterForm
)
from accounts.models import CustomUser


# ==================== DECORATORS ====================

def role_required(allowed_roles):
    """Decorator to restrict access based on user roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard_redirect')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def student_required(view_func):
    """Decorator for student-only views."""
    return role_required(['student'])(view_func)


def staff_required(view_func):
    """Decorator for staff-only views."""
    return role_required(['staff'])(view_func)


def admin_required(view_func):
    """Decorator for admin-only views."""
    return role_required(['admin'])(view_func)


# ==================== STUDENT VIEWS ====================

@login_required
@student_required
def student_create_complaint(request):
    """Allow students to create a new complaint."""
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.student = request.user
            complaint.save()
            messages.success(request, 'Your complaint has been submitted successfully!')
            return redirect('complaints:student_my_complaints')
    else:
        form = ComplaintForm()
    
    categories = Category.objects.filter(is_active=True)
    
    return render(request, 'complaints/student/create_complaint.html', {
        'form': form,
        'categories': categories,
    })


@login_required
@student_required
def student_my_complaints(request):
    """Display all complaints submitted by the logged-in student."""
    complaints = Complaint.objects.filter(student=request.user)
    
    # Apply filters
    filter_form = ComplaintFilterForm(request.GET)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        search = filter_form.cleaned_data.get('search')
        
        if status:
            complaints = complaints.filter(status=status)
        if priority:
            complaints = complaints.filter(priority=priority)
        if search:
            complaints = complaints.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
    
    # Pagination
    paginator = Paginator(complaints, 10)
    page = request.GET.get('page', 1)
    complaints_page = paginator.get_page(page)
    
    # Stats
    stats = {
        'total': Complaint.objects.filter(student=request.user).count(),
        'pending': Complaint.objects.filter(student=request.user, status='pending').count(),
        'in_progress': Complaint.objects.filter(student=request.user, status='in_progress').count(),
        'resolved': Complaint.objects.filter(student=request.user, status='resolved').count(),
    }
    
    return render(request, 'complaints/student/my_complaints.html', {
        'complaints': complaints_page,
        'filter_form': filter_form,
        'stats': stats,
    })


@login_required
@student_required
def student_complaint_detail(request, pk):
    """View details of a specific complaint."""
    complaint = get_object_or_404(Complaint, pk=pk, student=request.user)
    comments = complaint.comments.filter(is_internal=False)
    
    if request.method == 'POST':
        comment_form = ComplaintCommentForm(request.POST, user=request.user)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.complaint = complaint
            comment.author = request.user
            comment.is_internal = False
            comment.save()
            messages.success(request, 'Your comment has been added.')
            return redirect('complaints:student_complaint_detail', pk=pk)
    else:
        comment_form = ComplaintCommentForm(user=request.user)
    
    return render(request, 'complaints/student/complaint_detail.html', {
        'complaint': complaint,
        'comments': comments,
        'comment_form': comment_form,
    })


# ==================== STAFF VIEWS ====================

@login_required
@staff_required
def staff_assigned_complaints(request):
    """Display complaints assigned to the logged-in staff member."""
    complaints = Complaint.objects.filter(assigned_staff=request.user)
    unassigned = Complaint.objects.filter(
        assigned_staff__isnull=True,
        status=Complaint.Status.PENDING
    )
    
    # Apply filters
    filter_form = ComplaintFilterForm(request.GET)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        search = filter_form.cleaned_data.get('search')
        
        if status:
            complaints = complaints.filter(status=status)
            unassigned = unassigned.filter(status=status) if status == 'pending' else unassigned.none()
        if priority:
            complaints = complaints.filter(priority=priority)
            unassigned = unassigned.filter(priority=priority)
        if search:
            complaints = complaints.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
            unassigned = unassigned.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
    
    # Stats
    stats = {
        'assigned': Complaint.objects.filter(assigned_staff=request.user).count(),
        'in_progress': Complaint.objects.filter(
            assigned_staff=request.user, 
            status='in_progress'
        ).count(),
        'resolved_today': Complaint.objects.filter(
            assigned_staff=request.user,
            status='resolved',
            resolved_at__date=timezone.now().date()
        ).count(),
        'overdue': Complaint.objects.filter(
            assigned_staff=request.user,
            is_sla_breached=True,
            status__in=['pending', 'in_progress']
        ).count(),
    }
    
    # Pagination
    paginator = Paginator(complaints, 10)
    page = request.GET.get('page', 1)
    complaints_page = paginator.get_page(page)
    
    return render(request, 'complaints/staff/assigned_complaints.html', {
        'complaints': complaints_page,
        'unassigned': unassigned[:5],
        'filter_form': filter_form,
        'stats': stats,
    })


@login_required
@staff_required
def staff_update_complaint(request, pk):
    """Allow staff to update complaint status and add solution."""
    complaint = get_object_or_404(Complaint, pk=pk)
    
    # Check if assigned to this staff or unassigned
    if complaint.assigned_staff and complaint.assigned_staff != request.user:
        messages.error(request, 'This complaint is assigned to another staff member.')
        return redirect('complaints:staff_assigned_complaints')
    
    if request.method == 'POST':
        form = ComplaintStatusUpdateForm(request.POST, instance=complaint)
        comment_form = ComplaintCommentForm(request.POST, user=request.user)
        
        if form.is_valid():
            updated_complaint = form.save(commit=False)
            # Auto-assign if not assigned
            if not updated_complaint.assigned_staff:
                updated_complaint.assigned_staff = request.user
            updated_complaint.save()
            
            # Add comment if provided
            if comment_form.is_valid() and comment_form.cleaned_data.get('content'):
                comment = comment_form.save(commit=False)
                comment.complaint = complaint
                comment.author = request.user
                comment.save()
            
            messages.success(request, 'Complaint updated successfully!')
            return redirect('complaints:staff_assigned_complaints')
    else:
        form = ComplaintStatusUpdateForm(instance=complaint)
        comment_form = ComplaintCommentForm(user=request.user)
    
    comments = complaint.comments.all()
    
    return render(request, 'complaints/staff/update_status.html', {
        'complaint': complaint,
        'form': form,
        'comment_form': comment_form,
        'comments': comments,
    })


@login_required
@staff_required
def staff_claim_complaint(request, pk):
    """Allow staff to claim an unassigned complaint."""
    complaint = get_object_or_404(Complaint, pk=pk)
    
    if complaint.assigned_staff:
        messages.warning(request, 'This complaint is already assigned.')
    else:
        complaint.assigned_staff = request.user
        complaint.status = Complaint.Status.IN_PROGRESS
        complaint.save()
        messages.success(request, f'Complaint #{pk} has been assigned to you.')
    
    return redirect('complaints:staff_update_complaint', pk=pk)


# ==================== ADMIN VIEWS ====================

@login_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard with statistics and overview."""
    # Overall stats
    total_complaints = Complaint.objects.count()
    pending = Complaint.objects.filter(status='pending').count()
    in_progress = Complaint.objects.filter(status='in_progress').count()
    resolved = Complaint.objects.filter(status='resolved').count()
    escalated = Complaint.objects.filter(status='escalated').count()
    
    # SLA stats
    sla_breached = Complaint.objects.filter(is_sla_breached=True).count()
    overdue = Complaint.objects.filter(
        is_sla_breached=True,
        status__in=['pending', 'in_progress']
    ).count()
    
    # User stats
    total_students = CustomUser.objects.filter(role='student').count()
    total_staff = CustomUser.objects.filter(role='staff').count()
    
    # Recent complaints
    recent_complaints = Complaint.objects.all()[:10]
    
    # Staff performance
    staff_stats = CustomUser.objects.filter(role='staff').annotate(
        assigned_count=Count('assigned_complaints'),
        resolved_count=Count(
            'assigned_complaints',
            filter=Q(assigned_complaints__status='resolved')
        )
    ).order_by('-resolved_count')[:5]
    
    # Complaints by priority
    priority_stats = {
        'low': Complaint.objects.filter(priority='low').count(),
        'medium': Complaint.objects.filter(priority='medium').count(),
        'high': Complaint.objects.filter(priority='high').count(),
        'urgent': Complaint.objects.filter(priority='urgent').count(),
    }
    
    context = {
        'total_complaints': total_complaints,
        'pending': pending,
        'in_progress': in_progress,
        'resolved': resolved,
        'escalated': escalated,
        'sla_breached': sla_breached,
        'overdue': overdue,
        'total_students': total_students,
        'total_staff': total_staff,
        'recent_complaints': recent_complaints,
        'staff_stats': staff_stats,
        'priority_stats': priority_stats,
    }
    
    return render(request, 'complaints/admin/dashboard.html', context)


@login_required
@admin_required
def admin_escalations(request):
    """View and manage escalated complaints."""
    escalations = Escalation.objects.filter(resolved=False).select_related(
        'complaint', 'escalated_by', 'escalated_to'
    )
    resolved_escalations = Escalation.objects.filter(resolved=True).select_related(
        'complaint', 'escalated_by', 'escalated_to'
    )[:20]
    
    # Auto-escalation for SLA breaches
    overdue_complaints = Complaint.objects.filter(
        is_sla_breached=True,
        status__in=['pending', 'in_progress']
    ).exclude(
        escalations__resolved=False
    )
    
    return render(request, 'complaints/admin/escalations.html', {
        'escalations': escalations,
        'resolved_escalations': resolved_escalations,
        'overdue_complaints': overdue_complaints,
    })


@login_required
@admin_required
def admin_all_complaints(request):
    """View all complaints with filters."""
    complaints = Complaint.objects.all().select_related('student', 'assigned_staff')
    
    # Apply filters
    filter_form = ComplaintFilterForm(request.GET)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        search = filter_form.cleaned_data.get('search')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        
        if status:
            complaints = complaints.filter(status=status)
        if priority:
            complaints = complaints.filter(priority=priority)
        if search:
            complaints = complaints.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(student__username__icontains=search)
            )
        if date_from:
            complaints = complaints.filter(created_at__date__gte=date_from)
        if date_to:
            complaints = complaints.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(complaints, 20)
    page = request.GET.get('page', 1)
    complaints_page = paginator.get_page(page)
    
    return render(request, 'complaints/admin/all_complaints.html', {
        'complaints': complaints_page,
        'filter_form': filter_form,
    })


@login_required
@admin_required  
def admin_escalate_complaint(request, pk):
    """Create an escalation for a complaint."""
    complaint = get_object_or_404(Complaint, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'other')
        notes = request.POST.get('notes', '')
        
        Escalation.objects.create(
            complaint=complaint,
            escalated_by=request.user,
            reason=reason,
            notes=notes
        )
        
        complaint.status = Complaint.Status.ESCALATED
        complaint.save()
        
        messages.success(request, f'Complaint #{pk} has been escalated.')
    
    return redirect('complaints:admin_escalations')
