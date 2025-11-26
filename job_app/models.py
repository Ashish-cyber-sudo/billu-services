from django.db import models
from django.contrib.auth.models import User
import random
from django.utils import timezone
from django.db import models
from datetime import timedelta




class Profile(models.Model):
    ROLE_CHOICES = [
        ('provider', 'Provider'),
        ('service_seeker', 'Service Seeker'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=30, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    wallet_balance = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    is_phone_verified = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', default='profile_images/default.png', blank=True)


    def __str__(self):
        return f"{self.user.username} — {self.get_role_display()}"

class Service(models.Model):
    CATEGORY_CHOICES = [
        ('welder', 'Welder'),
        ('plumber', 'Plumber'),
        ('painter', 'Painter'),
        ('electrician', 'Electrician'),
        ('carpenter', 'Carpenter'),
        ('bike_mechanic', 'Bike Mechanic'),
        ('car_mechanic', 'Car Mechanic'),
        ('tyre_repair', 'Tyre Repairman'),
        ('waste_collector', 'Waste Collector'),
        ('pest_control', 'Pest Control'),
        ('cleaning', 'Cleaning Service'),
        ('gardening', 'Gardening Service'),
        ('painting', 'Painting Service'),
        ('moving', 'Moving Service'),
        ('delivery', 'Delivery Service'),
        ('tutor', 'Tutor'),
        ('driver', 'Driver'),
        ('chef', 'Chef'),
        ('babysitter', 'Babysitter'),
        ('maid', 'Maid'),
        ('security_guard', 'Security Guard'),
        ('photographer', 'Photographer'),
        ('event_planner', 'Event Planner'),
        ('female_tailor','Female Tailor'),
        ('men_tailor','men Tailor'),
    ]

    provider = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=120)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='service_images/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} — {self.get_category_display()}"

class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('ringing', 'Ringing'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('timeout', 'Timeout'),
    ]

    seeker = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='outgoing_requests')
    provider = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='incoming_requests')
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    radius = models.IntegerField(default=5)
    user_lat = models.FloatField(null=True, blank=True)
    user_lon = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ringing')
    created_at = models.DateTimeField(auto_now_add=True)
    is_adhar_verified = models.BooleanField(default=False)  # store seeker verification snapshot

    def __str__(self):
        return f"Request {self.id}: {self.seeker} -> {self.provider} ({self.service})"

# class Booking(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('confirmed', 'Confirmed'),
#         ('completed', 'Completed'),
#         ('cancelled', 'Cancelled'),
#     ]
#     seeker = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='bookings')
#     service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
#     address = models.CharField(max_length=300)
#     scheduled_for = models.DateTimeField()
#     notes = models.TextField(blank=True)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
#     worker = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True, related_name='worker_bookings')
#     date = models.DateField(default=timezone.now)
#     payment_id = models.CharField(max_length=100, blank=True, null=True)
#     is_paid = models.BooleanField(default=False)
#     def __str__(self):
#         return f"Booking #{self.pk} — {self.service} for {self.seeker.user.username}"


class SeekerBooking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    seeker = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="seeker_bookings")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="seeker_service_bookings")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SeekerBooking #{self.pk} — {self.service.title} by {self.seeker.user.username}"


class ProviderBooking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    provider = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="provider_bookings")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="provider_service_bookings")
    seeker = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="provider_seeker_bookings")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ProviderBooking #{self.pk} — {self.service.title} for {self.seeker.user.username}"
    

class PhoneOTP(models.Model):
    phone = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))
    
class Review(models.Model):
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=1)  # 1–5 stars
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer.username} - {self.rating}★"

    def stars(self):
        """Return star icons for display"""
        return '★' * self.rating + '☆' * (5 - self.rating)

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username}'s Wallet"
    

class WalletTransaction(models.Model):
    wallet = models.ForeignKey(
    Wallet,
    on_delete=models.CASCADE,
    related_name='transactions',
    null=True,
    blank=True
)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"