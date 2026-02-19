"""
Background tasks for complaints management.
These can be run with Django management commands or Celery.
"""

from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

from .models import Complaint, Escalation
from accounts.models import CustomUser

logger = logging.getLogger('complaints')


def check_sla_breaches():
    """
    Check for SLA breaches and mark complaints accordingly.
    This should be run periodically (e.g., every hour via cron or Celery).
    """
    now = timezone.now()
    
    # Find complaints that have breached SLA
    breached_complaints = Complaint.objects.filter(
        sla_deadline__lt=now,
        is_sla_breached=False,
        status__in=[Complaint.Status.PENDING, Complaint.Status.IN_PROGRESS]
    )
    
    count = 0
    for complaint in breached_complaints:
        complaint.is_sla_breached = True
        complaint.save(update_fields=['is_sla_breached', 'updated_at'])
        count += 1
        logger.warning(f"SLA breached for complaint #{complaint.id}")
    
    if count:
        logger.info(f"Marked {count} complaints as SLA breached")
    
    return count


def auto_escalate_overdue():
    """
    Auto-escalate complaints that are severely overdue.
    Escalate if past 2x the SLA deadline.
    """
    now = timezone.now()
    escalation_threshold = timedelta(hours=getattr(settings, 'SLA_RESOLUTION_TIME', 72) * 2)
    
    # Find severely overdue complaints without active escalations
    overdue_complaints = Complaint.objects.filter(
        is_sla_breached=True,
        status__in=[Complaint.Status.PENDING, Complaint.Status.IN_PROGRESS],
        created_at__lt=now - escalation_threshold
    ).exclude(
        escalations__resolved=False  # No active escalations
    )
    
    count = 0
    for complaint in overdue_complaints:
        Escalation.objects.create(
            complaint=complaint,
            reason=Escalation.Reason.SLA_BREACH,
            notes=f"Auto-escalated: Complaint unresolved for {escalation_threshold.days} days"
        )
        complaint.status = Complaint.Status.ESCALATED
        complaint.save(update_fields=['status', 'updated_at'])
        count += 1
        logger.warning(f"Auto-escalated complaint #{complaint.id}")
    
    if count:
        logger.info(f"Auto-escalated {count} severely overdue complaints")
    
    return count


def assign_pending_complaints():
    """
    Assign pending complaints to available staff.
    Uses round-robin assignment based on current workload.
    """
    pending = Complaint.objects.filter(
        assigned_staff__isnull=True,
        status=Complaint.Status.PENDING
    )
    
    if not pending.exists():
        return 0
    
    # Get staff ordered by current workload (ascending)
    staff_list = CustomUser.objects.filter(
        role=CustomUser.Role.STAFF,
        is_active=True
    ).annotate(
        workload=models.Count(
            'assigned_complaints',
            filter=models.Q(
                assigned_complaints__status__in=[
                    Complaint.Status.PENDING,
                    Complaint.Status.IN_PROGRESS
                ]
            )
        )
    ).order_by('workload')
    
    if not staff_list.exists():
        logger.warning("No available staff for complaint assignment")
        return 0
    
    count = 0
    staff_index = 0
    staff_count = staff_list.count()
    
    for complaint in pending:
        staff = staff_list[staff_index % staff_count]
        complaint.assigned_staff = staff
        complaint.save(update_fields=['assigned_staff', 'updated_at'])
        staff_index += 1
        count += 1
        logger.info(f"Assigned complaint #{complaint.id} to {staff.username}")
    
    return count


def generate_daily_stats():
    """
    Generate daily statistics for reporting.
    Returns a dictionary with various metrics.
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    stats = {
        'date': today.isoformat(),
        'total_complaints': Complaint.objects.count(),
        'created_today': Complaint.objects.filter(created_at__date=today).count(),
        'resolved_today': Complaint.objects.filter(resolved_at__date=today).count(),
        'pending': Complaint.objects.filter(status=Complaint.Status.PENDING).count(),
        'in_progress': Complaint.objects.filter(status=Complaint.Status.IN_PROGRESS).count(),
        'escalated': Complaint.objects.filter(status=Complaint.Status.ESCALATED).count(),
        'sla_breached_total': Complaint.objects.filter(is_sla_breached=True).count(),
        'active_escalations': Escalation.objects.filter(resolved=False).count(),
    }
    
    # Calculate average resolution time
    resolved = Complaint.objects.filter(
        resolved_at__isnull=False
    ).values_list('created_at', 'resolved_at')
    
    if resolved:
        total_time = sum(
            (r[1] - r[0]).total_seconds() for r in resolved
        )
        avg_time = total_time / len(resolved) / 3600  # Convert to hours
        stats['avg_resolution_hours'] = round(avg_time, 2)
    else:
        stats['avg_resolution_hours'] = 0
    
    logger.info(f"Daily stats generated: {stats}")
    return stats
