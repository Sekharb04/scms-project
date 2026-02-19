"""
URL patterns for accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Student URLs
    path('student/register/', views.student_register, name='student_register'),
    path('studentlogin/', views.student_login, name='student_login'),

    # Staff URLs
    path('stafflogin/', views.staff_login, name='staff_login'),

    # Admin URLs
    path('adminlogin/', views.admin_login, name='admin_login'),

    # Common URLs
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('logout/', views.user_logout, name='logout'),
]
