from django.urls import path
from . import views
from django.http import JsonResponse


app_name = 'job_app'

def chrome_devtools_ignore(request):
    return JsonResponse({}, status=204)

urlpatterns = [
    # path('', views.base, name='base'),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('login/', views.request_otp, name='request_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('provider/service/add/', views.service_create, name='service_add'),
    path('provider/service/<int:pk>/edit/', views.service_update, name='service_edit'),
    path('provider/service/<int:pk>/delete/', views.service_delete, name='service_delete'),

    # path('seeker/dashboard/', views.seeker_dashboard, name='seeker_dashboard'),

    path('services/', views.service_list, name='service_list'),
    path('services/<int:pk>/', views.service_detail, name='service_detail'),
    path('services/<int:pk>/book/', views.book_service, name='service_book'),

    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),

    path("search-suggestions/", views.service_search_suggestions, name="search_suggestions"),
    path('otp-login/', views.otp_login, name='otp_login'),
    path('request-otp/', views.request_otp, name='request_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('my-bookings/', views.user_bookings, name='user_bookings'),
    path('profile-settings/', views.profile_settings, name='profile_settings'),

    path("payment/<int:service_id>/", views.create_payment, name="create_payment"),
    path("payment-success/<int:booking_id>/", views.payment_success, name="payment_success"),
    path('wallet/', views.wallet_view, name='wallet'),
    path('wallet/add/', views.add_money, name='add_money'),
    path('wallet/success/', views.payment_success, name='payment_success'),

    path(".well-known/appspecific/com.chrome.devtools.json", chrome_devtools_ignore),
    path('send-requests/', views.send_requests, name='send_requests'),
    # path("bookings/", views.bookings_view, name="bookings"),
    path("bookings/create/", views.create_booking, name="create_booking"),
    path("bookings/seeker/", views.seeker_bookings_view, name="seeker_bookings"),
    path("bookings/provider/", views.provider_bookings_view, name="provider_bookings"),
]
