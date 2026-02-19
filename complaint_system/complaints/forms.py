"""
Forms for complaints app.
"""

from django import forms
from .models import Complaint, ComplaintComment, Category


class ComplaintForm(forms.ModelForm):
    """Form for creating/editing complaints."""
    
    class Meta:
        model = Complaint
        fields = ['title', 'category', 'priority', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title for your complaint'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your complaint in detail...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].required = False
        self.fields['priority'].initial = Complaint.Priority.MEDIUM


class ComplaintStatusUpdateForm(forms.ModelForm):
    """Form for staff to update complaint status."""
    
    class Meta:
        model = Complaint
        fields = ['status', 'solution', 'assigned_staff']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'solution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter the solution or update...'
            }),
            'assigned_staff': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import CustomUser
        self.fields['assigned_staff'].queryset = CustomUser.objects.filter(
            role=CustomUser.Role.STAFF, 
            is_active=True
        )
        self.fields['assigned_staff'].required = False


class ComplaintCommentForm(forms.ModelForm):
    """Form for adding comments to complaints."""
    
    class Meta:
        model = ComplaintComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a comment or update...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Students shouldn't see internal note option
        if user and user.is_student:
            del self.fields['is_internal']


class ComplaintFilterForm(forms.Form):
    """Form for filtering complaints."""
    
    STATUS_CHOICES = [('', 'All Statuses')] + list(Complaint.Status.choices)
    PRIORITY_CHOICES = [('', 'All Priorities')] + list(Complaint.Priority.choices)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search complaints...'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
