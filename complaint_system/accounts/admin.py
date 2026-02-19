"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model."""
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 
                    'department', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'department', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'student_id']
    ordering = ['-created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'department', 'student_id')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'email', 'first_name', 'last_name', 
                      'phone', 'department', 'student_id')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(role__in=['student', 'staff'])
