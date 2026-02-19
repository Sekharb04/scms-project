"""
URL patterns for complaints app.
"""

from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    # Student URLs
    path('create/', views.student_create_complaint, name='student_create_complaint'),
    path('my-complaints/', views.student_my_complaints, name='student_my_complaints'),
    path('my-complaints/<int:pk>/', views.student_complaint_detail, name='student_complaint_detail'),
    
    # Staff URLs
    path('staff/assigned/', views.staff_assigned_complaints, name='staff_assigned_complaints'),
    path('staff/update/<int:pk>/', views.staff_update_complaint, name='staff_update_complaint'),
    path('staff/claim/<int:pk>/', views.staff_claim_complaint, name='staff_claim_complaint'),
    
    # Admin URLs
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/escalations/', views.admin_escalations, name='admin_escalations'),
    path('admin-panel/all/', views.admin_all_complaints, name='admin_all_complaints'),
    path('admin-panel/escalate/<int:pk>/', views.admin_escalate_complaint, name='admin_escalate_complaint'),
]
