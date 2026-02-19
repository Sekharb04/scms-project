"""
Admin configuration for complaints app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Complaint, Category, SLA, Escalation, ComplaintComment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'student', 'assigned_staff', 'status_badge', 
        'priority_badge', 'is_sla_breached', 'created_at'
    ]
    list_filter = ['status', 'priority', 'is_sla_breached', 'category', 'created_at']
    search_fields = ['title', 'description', 'student__username', 'assigned_staff__username']
    raw_id_fields = ['student', 'assigned_staff']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at', 'is_sla_breached']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Complaint Details', {
            'fields': ('title', 'description', 'category', 'priority')
        }),
        ('Assignment', {
            'fields': ('student', 'assigned_staff', 'status')
        }),
        ('Resolution', {
            'fields': ('solution', 'resolved_at')
        }),
        ('SLA', {
            'fields': ('sla_deadline', 'is_sla_breached'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'in_progress': 'blue',
            'resolved': 'green',
            'escalated': 'red',
            'closed': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {
            'low': 'gray',
            'medium': 'blue',
            'high': 'orange',
            'urgent': 'red',
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student', 'assigned_staff', 'category')


@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ['name', 'priority', 'response_time_hours', 'resolution_time_hours', 'is_active']
    list_filter = ['priority', 'is_active']
    ordering = ['priority']


@admin.register(Escalation)
class EscalationAdmin(admin.ModelAdmin):
    list_display = ['id', 'complaint', 'reason', 'escalated_by', 'resolved', 'created_at']
    list_filter = ['reason', 'resolved', 'created_at']
    search_fields = ['complaint__title', 'notes']
    raw_id_fields = ['complaint', 'escalated_by', 'escalated_to']
    readonly_fields = ['created_at', 'resolved_at']
    ordering = ['-created_at']


@admin.register(ComplaintComment)
class ComplaintCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'complaint', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['content', 'author__username']
    raw_id_fields = ['complaint', 'author']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
