from django.contrib import admin
from .models import Profile, Service, SeekerBooking, ProviderBooking, Review
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


# ---------------------------
# Profile + User integration
# ---------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'is_phone_verified', 'location')
    list_filter = ('role', 'is_phone_verified')
    search_fields = ('user__username', 'phone', 'location')
    list_editable = ('role',)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


# Unregister the original User admin and re-register the extended one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ---------------------------
# Service
# ---------------------------
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'provider', 'hourly_rate', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'provider__user__username')
    list_editable = ('is_active',)
    ordering = ('-created_at',)


# ---------------------------
# SeekerBooking
# ---------------------------
@admin.register(SeekerBooking)
class SeekerBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'seeker', 'service', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('seeker__user__username', 'service__title')


# ---------------------------
# ProviderBooking
# ---------------------------
@admin.register(ProviderBooking)
class ProviderBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'seeker', 'service', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('provider__user__username', 'seeker__user__username', 'service__title')


# ---------------------------
# Review
# ---------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('service', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('service__title', 'reviewer__username', 'comment')
