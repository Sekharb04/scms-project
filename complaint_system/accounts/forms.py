"""
Forms for user authentication and registration.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser


class StudentRegistrationForm(UserCreationForm):
    """Registration form for students."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    student_id = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Student ID'
        })
    )
    department = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Department'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (optional)'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 
                  'student_id', 'department', 'phone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if CustomUser.objects.filter(student_id=student_id).exists():
            raise ValidationError('This Student ID is already registered.')
        return student_id
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.STUDENT
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    """Custom login form with Bootstrap styling."""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class StudentLoginForm(CustomLoginForm):
    """Login form for students."""
    
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.role != CustomUser.Role.STUDENT:
            raise ValidationError(
                'This login is for students only. Please use the appropriate login page.',
                code='invalid_role'
            )


class StaffLoginForm(CustomLoginForm):
    """Login form for staff members."""
    
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.role != CustomUser.Role.STAFF:
            raise ValidationError(
                'This login is for staff only. Please use the appropriate login page.',
                code='invalid_role'
            )


class AdminLoginForm(CustomLoginForm):
    """Login form for administrators."""
    
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.role != CustomUser.Role.ADMIN:
            raise ValidationError(
                'This login is for administrators only. Please use the appropriate login page.',
                code='invalid_role'
            )
