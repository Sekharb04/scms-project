"""
Models for the Complaints Management System.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Category(models.Model):
    """Categories for complaints."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Complaint(models.Model):
    """Main complaint model."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        ESCALATED = 'escalated', 'Escalated'
        CLOSED = 'closed', 'Closed'
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'
    
    # Relationships
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_complaints',
        limit_choices_to={'role': 'student'}
    )
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        limit_choices_to={'role': 'staff'}
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints'
    )
    
    # Complaint details
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    solution = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # SLA tracking
    sla_deadline = models.DateTimeField(null=True, blank=True)
    is_sla_breached = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'
    
    def __str__(self):
        return f"#{self.id} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Set SLA deadline on creation
        if not self.pk and not self.sla_deadline:
            self.sla_deadline = timezone.now() + timedelta(
                hours=getattr(settings, 'SLA_RESOLUTION_TIME', 72)
            )
        
        # Set resolved_at when status changes to resolved
        if self.status == self.Status.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        # Check SLA breach
        if self.sla_deadline and timezone.now() > self.sla_deadline:
            self.is_sla_breached = True
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if complaint is overdue based on SLA."""
        if self.sla_deadline and self.status not in [self.Status.RESOLVED, self.Status.CLOSED]:
            return timezone.now() > self.sla_deadline
        return False
    
    @property
    def time_to_resolve(self):
        """Calculate time taken to resolve (if resolved)."""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None
    
    @property
    def status_badge_class(self):
        """Return Bootstrap badge class based on status."""
        status_classes = {
            self.Status.PENDING: 'bg-warning',
            self.Status.IN_PROGRESS: 'bg-info',
            self.Status.RESOLVED: 'bg-success',
            self.Status.ESCALATED: 'bg-danger',
            self.Status.CLOSED: 'bg-secondary',
        }
        return status_classes.get(self.status, 'bg-secondary')


class SLA(models.Model):
    """SLA configuration model."""
    
    name = models.CharField(max_length=100)
    priority = models.CharField(
        max_length=10,
        choices=Complaint.Priority.choices,
        unique=True
    )
    response_time_hours = models.PositiveIntegerField(
        help_text='Time in hours to first response'
    )
    resolution_time_hours = models.PositiveIntegerField(
        help_text='Time in hours to resolution'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'SLA'
        verbose_name_plural = 'SLAs'
    
    def __str__(self):
        return f"{self.name} - {self.get_priority_display()}"


class Escalation(models.Model):
    """Track complaint escalations."""
    
    class Reason(models.TextChoices):
        SLA_BREACH = 'sla_breach', 'SLA Breach'
        CUSTOMER_REQUEST = 'customer_request', 'Customer Request'
        COMPLEXITY = 'complexity', 'High Complexity'
        UNRESOLVED = 'unresolved', 'Unresolved for Long Time'
        OTHER = 'other', 'Other'
    
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='escalations'
    )
    escalated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='escalations_made'
    )
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalations_received'
    )
    reason = models.CharField(
        max_length=20,
        choices=Reason.choices,
        default=Reason.SLA_BREACH
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Escalation'
        verbose_name_plural = 'Escalations'
    
    def __str__(self):
        return f"Escalation #{self.id} for Complaint #{self.complaint.id}"
    
    def save(self, *args, **kwargs):
        if self.resolved and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)


class ComplaintComment(models.Model):
    """Comments/updates on complaints."""
    
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    content = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text='Internal notes visible only to staff'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author} on Complaint #{self.complaint.id}"
