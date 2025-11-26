from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages,admin
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from math import radians, cos, sin, asin, sqrt
from .models import Profile, Service, SeekerBooking, ProviderBooking
from .models import Review, WalletTransaction
from .models import PhoneOTP
from .models import ServiceRequest
from twilio.rest import Client
from .forms import RegisterForm, ServiceForm, SeekerBookingForm, ProviderBookingForm

from geopy.distance import geodesic
from .forms import ReviewForm
from .utils import calculate_distance 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from job_app.utils import calculate_distance
from django.apps import apps 
import uuid
import random
import json
import razorpay


@property
def average_rating(self):
    reviews = self.reviews.all()
    if not reviews.exists():
        return 0
    return round(sum(r.rating for r in reviews) / reviews.count(), 1)

@property
def total_reviews(self):
    return self.reviews.count()


def create_payment(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    profile = request.user.profile

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    amount = int(service.hourly_rate * 100)  # in paise
    currency = "INR"

    # Create Razorpay order
    order = client.order.create(dict(amount=amount, currency=currency, payment_capture='1'))

    booking = Booking.objects.create(
        seeker=profile,
        service=service,
        address="",
        scheduled_for=timezone.now(),
        notes="",
        user=request.user,
    )

    booking.payment_id = order["id"]
    booking.save()

    context = {
        "service": service,
        "order_id": order["id"],
        "amount": amount,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "booking": booking,
    }

    return render(request, "job_app/payment.html", context)

@csrf_exempt
def payment_success(request, booking_id):
    payment_id = request.GET.get("payment_id")
    booking = get_object_or_404(Booking, id=booking_id)
    booking.payment_id = payment_id
    booking.is_paid = True
    booking.status = "confirmed"
    booking.save()
    messages.success(request, "Payment successful! Booking confirmed.")
    return redirect("job_app:user_dashboard")
    

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def wallet_view(request):
    profile = request.user.profile
    transactions = profile.transactions.all().order_by('-created_at')
    return render(request, 'job_app/wallet.html', {'profile': profile, 'transactions': transactions})


def add_money(request):
    if request.method == "POST":
        amount = int(request.POST.get("amount")) * 100  # Convert to paise
        payment = razorpay_client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": "1"
        })
        return render(request, "job_app/add_money.html", {
            "payment": payment,
            "amount": amount // 100,
            "razorpay_key": settings.RAZORPAY_KEY_ID
        })
    return redirect('job_app:wallet')


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        user = request.user
        profile = user.profile
        amount = int(request.POST.get('amount'))

        profile.wallet_balance += amount
        profile.save()

        WalletTransaction.objects.create(
            profile=profile,
            amount=amount,
            transaction_type='credit',
            description="Added to wallet"
        )

        messages.success(request, f"₹{amount} added to your wallet successfully!")
        return redirect('job_app:wallet')

def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    amount = booking.service.hourly_rate  # Or total booking amount

    provider_wallet = booking.worker.user.wallet

    # Credit provider's wallet
    provider_wallet.balance += Decimal(amount)
    provider_wallet.save()

    # Record transaction
    WalletTransaction.objects.create(
        wallet=provider_wallet,
        amount=amount,
        transaction_type='credit',
        description=f'Payment received for booking #{booking.id}'
    )

    # Optionally mark booking as paid
    booking.status = 'completed'
    booking.save()

    return redirect('job_app:seeker_dashboard')  
    
# ----------------- Public Home Page -----------------
def home(request):
    services = Service.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'job_app/home.html', {'services': services})


# ----------------- Registration -----------------

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        role = request.POST.get("role")
        phone = request.POST.get("phone")
        location = request.POST.get("location")
        latitude = request.POST.get("latitude") or None
        longitude = request.POST.get("longitude") or None

        # ✅ Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "❌ Username already taken. Please choose another.")
            return redirect("job_app:register")

        # ✅ Check if email already exists (optional but recommended)
        if User.objects.filter(email=email).exists():
            messages.error(request, "❌ Email already registered. Please log in instead.")
            return redirect("job_app:login")

        # ✅ Create user safely
        user = User.objects.create_user(username=username, email=email, password=password)

        # ✅ Create profile linked to user
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                "role": role,
                "phone": phone,
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
            }
        )
        
        if not created:
            # Update existing profile if needed
            profile.role = role
            profile.phone = phone
            profile.location = location
            profile.latitude = latitude
            profile.longitude = longitude
            profile.save()

        messages.success(request, "✅ Registration successful! Please log in.")
        return redirect("job_app:login")

    return render(request, "job_app/register.html")



# ----------------- Login / Logout -----------------
def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username')  # could be username or phone
        password = request.POST.get('password')

        user = None

        # 🔹 First, try to authenticate by username
        user = authenticate(request, username=identifier, password=password)

        # 🔹 If not found, try to authenticate using phone number
        if user is None:
            try:
                profile = Profile.objects.get(phone=identifier)
                user = authenticate(request, username=profile.user.username, password=password)
            except Profile.DoesNotExist:
                user = None

        # 🔹 Successful login
        if user:
            login(request, user)
            profile = Profile.objects.get(user=user)
            if profile.role == 'provider':
                return redirect('job_app:provider_dashboard')
            return redirect('job_app:user_dashboard')

        # 🔹 Invalid login
        return render(request, 'job_app/login.html', {'error': 'Invalid credentials. Please check username/phone and password.'})

    return render(request, 'job_app/login.html')


def logout_view(request):
    logout(request)
    return redirect('job_app:home')


# ----------------- Provider Dashboard -----------------
@login_required
def provider_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user, role='provider')
    services = profile.services.all()
    return render(request, 'job_app/provider_dashboard.html', {'services': services})

# ----------------- Job Seeker Dashboard -----------------
@login_required
def user_dashboard(request):
    return render(request, 'job_app/user_dashboard.html')


@login_required
def user_bookings(request):
    profile = request.user.profile

    if profile.role == "service_seeker":
        # Show bookings made by the seeker
        bookings = SeekerBooking.objects.filter(seeker=profile).order_by("-created_at")
        template = "job_app/seeker_bookings.html"
    else:
        # Show bookings assigned to the provider
        bookings = ProviderBooking.objects.filter(provider=profile).order_by("-created_at")
        template = "job_app/provider_bookings.html"

    return render(request, template, {
        "bookings": bookings,
        "section": "bookings"
    })


@login_required
def profile_settings(request):
    profile = request.user.profile

    if request.method == "POST":
        profile.phone = request.POST.get("phone", "")
        profile.location = request.POST.get("location", "")
        profile.latitude = request.POST.get("latitude") or None
        profile.longitude = request.POST.get("longitude") or None
        profile.role = request.POST.get("role", profile.role)

        if "profile_image" in request.FILES:
            profile.profile_image = request.FILES["profile_image"]

        profile.save()
        messages.success(request, "✅ Profile updated successfully!")
        return redirect("job_app:profile_settings")

    return render(request, "job_app/profile_settings.html", {
        "profile": profile,
        "section": "profile"
    })

    
# @login_required
# def seeker_dashboard(request):
#     profile = get_object_or_404(Profile, user=request.user, role='job_seeker')
#     bookings = profile.bookings.select_related('service').all()
#     return render(request, 'job_app/seeker_dashboard.html', {'bookings': bookings})


# ----------------- Service CRUD (Provider Only) -----------------
@login_required
def service_create(request):
    profile = get_object_or_404(Profile, user=request.user, role='provider')
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.provider = profile
            service.save()
            return redirect('job_app:provider_dashboard')
    else:
        form = ServiceForm()

    return render(request, 'job_app/service_form.html', {'form': form})


@login_required
def service_update(request, pk):
    profile = get_object_or_404(Profile, user=request.user, role='provider')
    service = get_object_or_404(Service, pk=pk, provider=profile)

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            return redirect('job_app:provider_dashboard')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'job_app/service_form.html', {'form': form, 'service': service})


@login_required
def service_delete(request, pk):
    profile = get_object_or_404(Profile, user=request.user, role='provider')
    service = get_object_or_404(Service, pk=pk, provider=profile)

    if request.method == 'POST':
        service.delete()
        return redirect('job_app:provider_dashboard')

    return render(request, 'job_app/service_form.html', {'service': service, 'confirm_delete': True})

def service_categories(request):
    return {
        'service_categories': Service.CATEGORY_CHOICES
    }

# ----------------- Service Listing + Search + Category + Radius Filter ----------------- # <-- Make sure utils.py exists (see below)


def service_list(request):
    services = Service.objects.filter(is_active=True)
    search = request.GET.get("search", "")
    category = request.GET.get("category", "")
    radius = request.GET.get("radius", "")
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if search:
        services = services.filter(title__icontains=search)

    if category:
        services = services.filter(category=category)

    # Attach distance
    if lat and lon:
        lat = float(lat)
        lon = float(lon)

        for s in services:
            if s.provider.latitude and s.provider.longitude:
                s.distance = calculate_distance(lat, lon, s.provider.latitude, s.provider.longitude)
            else:
                s.distance = None

        if radius:
            radius = float(radius)
            services = [s for s in services if s.distance and s.distance <= radius]

        services = sorted(services, key=lambda x: x.distance or 99999)

    return render(request, "job_app/service_list.html", {"services": services})


@login_required
def send_requests(request):
    try:
        data = json.loads(request.body)

        service_id = data["service_id"]
        lat = float(data["lat"])
        lon = float(data["lon"])
        radius = int(data["radius"])

        seeker = request.user.profile
        service = get_object_or_404(Service, id=service_id)

        providers = Profile.objects.filter(role="provider")
        channel_layer = get_channel_layer()

        sent_count = 0

        for p in providers:
            if p.latitude and p.longitude:
                dist = calculate_distance(lat, lon, p.latitude, p.longitude)
                if dist <= radius:
                    provider = service.provider  # assuming Service has a FK to Profile
                    req = ServiceRequest.objects.create(
                            seeker=seeker,
                            provider=provider,
                            service=service,
                            radius=radius
                        )

                    async_to_sync(channel_layer.group_send)(
                        f"provider_{provider.id}",
                        {
                            "type": "incoming_request",
                            "request_id": req.id,
                            "service": req.service.title,
                            "seeker": req.seeker.user.username,
                            "phone": req.seeker.phone
                        }
                    )
                    sent_count += 1

        return JsonResponse({"success": True, "sent_count": sent_count})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

# ----------------- Service Detail + Booking -----------------
@login_required
def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk, is_active=True)
    reviews = service.reviews.select_related('reviewer__profile')

    # Handle review submission
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.service = service
            review.reviewer = request.user
            review.save()
            messages.success(request, "Thanks for your feedback!")
            return redirect('job_app:service_detail', pk=service.pk)
    else:
        form = ReviewForm()

    context = {
        'service': service,
        'reviews': reviews,
        'form': form,
    }
    return render(request, 'job_app/service_detail.html', context)

@login_required
def book_service(request, pk):
    service = get_object_or_404(Service, pk=pk)
    seeker_profile = get_object_or_404(Profile, user=request.user, role='service_seeker')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.seeker = seeker_profile
            booking.service = service
            booking.save()
            return redirect('job_app:user_dashboard')
    else:
        form = BookingForm()

    return render(request, 'job_app/booking_confirm.html', {'form': form, 'service': service})

@login_required
def seeker_bookings_view(request):
    bookings = SeekerBooking.objects.filter(seeker=request.user.profile).order_by("-created_at")
    return render(request, "job_app/seeker_bookings.html", {"bookings": bookings, "section": "bookings"})

@login_required
def provider_bookings_view(request):
    bookings = ProviderBooking.objects.filter(provider=request.user.profile).order_by("-created_at")
    return render(request, "job_app/provider_bookings.html", {"bookings": bookings, "section": "bookings"})
    

@login_required
def bookings_view(request):
    profile = request.user.profile
    if profile.role == "service_seeker":
        bookings = SeekerBooking.objects.filter(seeker=profile).order_by("-created_at")
        template = "job_app/seeker_bookings.html"
    else:  # provider
        bookings = ProviderBooking.objects.filter(provider=profile).order_by("-created_at")
        template = "job_app/provider_bookings.html"

    return render(request, template, {
        "bookings": bookings,
        "section": "bookings"
    })

@csrf_exempt
def create_booking(request):
    if request.method == "POST":
        data = json.loads(request.body)
        request_id = data.get("request_id")
        status = data.get("status")

        ServiceRequest = apps.get_model("job_app", "ServiceRequest")
        Booking = apps.get_model("job_app", "Booking")
        Profile = apps.get_model("job_app", "Profile")

        try:
            service_request = ServiceRequest.objects.get(id=request_id)

            # Create booking using fields available in ServiceRequest
            booking = Booking.objects.create(
                service=service_request.service,
                seeker=service_request.seeker,   # Profile
                worker=request.user.profile,     # Provider Profile
                status=status,
                # Fill required fields with safe defaults if not in ServiceRequest
                address=getattr(service_request, "address", "Not Provided"),
                scheduled_for=getattr(service_request, "scheduled_for", None),
                notes=getattr(service_request, "notes", ""),
            )
            return JsonResponse({"success": True, "booking_id": booking.id})
        except ServiceRequest.DoesNotExist:
            return JsonResponse({"success": False, "error": "ServiceRequest not found"}, status=404)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)





# Simple success/cancel endpoints

def payment_success(request):
    return render(request, 'job_app/payment_success.html')

def payment_cancel(request):
    return render(request, 'job_app/payment_cancel.html')

def about(request):
    return render(request, 'job_app/about.html')

def contact(request):
    success = False
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject", "Contact Form Message")
        message = request.POST.get("message")

        full_message = f"New message from {name} ({email}):\n\n{message}"

        try:
            send_mail(subject, full_message, settings.DEFAULT_FROM_EMAIL, ["support@jobportal.com"])
            success = True
        except Exception as e:
            print("Email send failed:", e)

    return render(request, "job_app/contact.html", {"success": success})

def service_search_suggestions(request):
    query = request.GET.get("q", "")
    results = []

    if query:
        services = Service.objects.filter(title__icontains=query).select_related("provider__user")[:5]
        for s in services:
            results.append({
                "name": s.title,
                "provider": s.provider.user.username,
                "url": reverse("job_app:service_detail", args=[s.id])
            })

    return JsonResponse({"results": results})

def otp_login(request):
    return render(request, 'job_app/otp_login.html')


def request_otp(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')

        # check if user exists
        try:
            profile = Profile.objects.get(phone=phone)
        except Profile.DoesNotExist:
            messages.error(request, "No account with this phone number. Please register first.")
            return redirect('job_app:register')

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        profile.otp = otp
        profile.save()

        # Store phone in session
        request.session['otp_phone'] = phone 
        
        if not phone.startswith("+"):
            phone = "+91" + phone  # <-- Change this to your country code

        request.session["phone"] = phone 

        # Send OTP via Twilio
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"Your OTP is {otp}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
        except Exception as e:
            print("Twilio Error:", e)
            messages.warning(request, f"SMS Failed (DEV Mode) — OTP is: {otp}")

        return redirect('job_app:verify_otp')

    return redirect('job_app:otp_login')


def verify_otp(request):
    phone = request.session.get('otp_phone')  # Retrieve stored phone
    if not phone:
        messages.error(request, "Session expired. Try again.")
        return redirect('job_app:otp_login')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        profile = Profile.objects.get(phone=phone)

        if profile.otp == entered_otp:
            profile.is_phone_verified = True
            profile.save()
            login(request, profile.user)
            messages.success(request, "Successfully logged in!")
            return redirect('job_app:service_list')
        else:
            messages.error(request, "Incorrect OTP. Try again.")

    return render(request, 'job_app/verify_otp.html')




