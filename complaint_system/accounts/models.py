"""
Custom User Model for Student Complaint Management System
Supports roles: STUDENT, STAFF, ADMIN
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom User model with role-based access control.
    """
    
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        STAFF = 'staff', 'Staff'
        ADMIN = 'admin', 'Admin'
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text='User role determines access level'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF
    
    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN
    
    def get_dashboard_url(self):
        """Return the appropriate dashboard URL based on role."""
        from django.urls import reverse
        if self.is_student:
            return reverse('complaints:student_my_complaints')
        elif self.is_staff_member:
            return reverse('complaints:staff_assigned_complaints')
        elif self.is_admin_user:
            return reverse('complaints:admin_dashboard')
        return reverse('home')
