from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Profile, Service, SeekerBooking, ProviderBooking, Review


class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('provider', 'Provider'),
        ('service_seeker', 'Service Seeker'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    phone = forms.CharField(required=False)
    location = forms.CharField(required=False)
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password1', 'password2',
            'role', 'phone', 'location', 'latitude', 'longitude'
        ]


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'category', 'description', 'hourly_rate', 'image', 'is_active']


# ---------------------------
# Seeker Booking Form
# ---------------------------
class SeekerBookingForm(forms.ModelForm):
    class Meta:
        model = SeekerBooking
        fields = ['service', 'status']  # adjust if you want more fields


# ---------------------------
# Provider Booking Form
# ---------------------------
class ProviderBookingForm(forms.ModelForm):
    class Meta:
        model = ProviderBooking
        fields = ['service', 'seeker', 'status']  # adjust if you want more fields


# ---------------------------
# Profile Form
# ---------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'location', 'profile_image']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }


# ---------------------------
# Review Form
# ---------------------------
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} ★') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your review...'}
            ),
        }
