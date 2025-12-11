from django import forms
from .models import AuthorizedPerson

class AuthorizedPersonForm(forms.ModelForm):
    """Form for authorized person with multiple photo support"""
    
    additional_photos = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'multiple': True,
            'accept': 'image/*',
            'class': 'form-control'
        }),
        help_text='You can upload multiple photos of the same person for better recognition'
    )
    
    class Meta:
        model = AuthorizedPerson
        fields = ['name', 'email', 'phone', 'role', 'photo', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Full Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'role': 'Role/Position',
            'photo': 'Primary Photo',
            'is_active': 'Is Active',
        }
