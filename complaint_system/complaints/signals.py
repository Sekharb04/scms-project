"""
Django signals for complaints app.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Complaint, Escalation, SLA

logger = logging.getLogger('complaints')


@receiver(post_save, sender=Complaint)
def complaint_created(sender, instance, created, **kwargs):
    """Handle actions when a new complaint is created."""
    if created:
        logger.info(f"New complaint created: #{instance.id} by {instance.student.username}")
        
        # Set SLA deadline based on priority if SLA exists
        try:
            sla = SLA.objects.get(priority=instance.priority, is_active=True)
            instance.sla_deadline = timezone.now() + timedelta(hours=sla.resolution_time_hours)
            # Use update to avoid triggering signal again
            Complaint.objects.filter(pk=instance.pk).update(
                sla_deadline=instance.sla_deadline
            )
        except SLA.DoesNotExist:
            pass


@receiver(pre_save, sender=Complaint)
def complaint_status_changed(sender, instance, **kwargs):
    """Track status changes and handle related actions."""
    if instance.pk:
        try:
            old_instance = Complaint.objects.get(pk=instance.pk)
            
            # Status changed
            if old_instance.status != instance.status:
                logger.info(
                    f"Complaint #{instance.id} status changed: "
                    f"{old_instance.status} -> {instance.status}"
                )
                
                # Auto-set resolved_at when resolved
                if instance.status == Complaint.Status.RESOLVED:
                    instance.resolved_at = timezone.now()
                
                # Check for SLA breach when escalating
                if instance.status == Complaint.Status.ESCALATED:
                    if instance.is_sla_breached:
                        logger.warning(f"Complaint #{instance.id} escalated due to SLA breach")
            
            # Staff assignment changed
            if old_instance.assigned_staff != instance.assigned_staff:
                if instance.assigned_staff:
                    logger.info(
                        f"Complaint #{instance.id} assigned to {instance.assigned_staff.username}"
                    )
        except Complaint.DoesNotExist:
            pass


@receiver(post_save, sender=Escalation)
def escalation_created(sender, instance, created, **kwargs):
    """Handle actions when a complaint is escalated."""
    if created:
        logger.warning(
            f"Escalation created for Complaint #{instance.complaint.id}: "
            f"{instance.get_reason_display()}"
        )
        
        # Update complaint status if not already escalated
        complaint = instance.complaint
        if complaint.status != Complaint.Status.ESCALATED:
            complaint.status = Complaint.Status.ESCALATED
            complaint.save(update_fields=['status', 'updated_at'])
