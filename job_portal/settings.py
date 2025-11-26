from pathlib import Path
import os
from decouple import config
import dj_database_url
# ---------------------------------------------------
# BASE DIRECTORY
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------
# SECURITY
# ---------------------------------------------------
SECRET_KEY = 'django-insecure-please-change-me'
DEBUG = True
ALLOWED_HOSTS = ["*", ".onrender.com", 'localhost', '127.0.0.1','192.168.16.1']

CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com"
]


# ---------------------------------------------------
# INSTALLED APPS
# ---------------------------------------------------
INSTALLED_APPS = [
    'channels',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    
    
    # Third-party
    'crispy_forms',
    'crispy_bootstrap5',

    # Project Apps
    'job_app.apps.JobAppConfig',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/otp-login/'

# ---------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'job_portal.urls'

# ---------------------------------------------------
# TEMPLATES
# ---------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ---------------------------------------------------
# DATABASE
# ---------------------------------------------------
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


DATABASES = {
    'default': dj_database_url.config(default=os.environ.get("postgresql://billu_service_user:iHc1arcc9yrdaM5eXTGNqrFHEsxgeR5E@dpg-d4jbl8gbdp1s73fqqrmg-a/billu_service"))
}
AUTH_PASSWORD_VALIDATORS = []

# ---------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------
# STATIC FILES
# ---------------------------------------------------
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "job_portal" / "static",   # keep only real folders
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------------------------------------------------
# MEDIA FILES
# ---------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------
# PAYMENTS (dummy for now)
# ---------------------------------------------------
STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
RAZORPAY_KEY_ID = config("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = config("RAZORPAY_KEY_SECRET", default="")

# ---------------------------------------------------
# TWILIO & AADHAR
# ---------------------------------------------------
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default="")
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default="")
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default="")

UIDAI_AUTH_URL = config('UIDAI_AUTH_URL', default="")
UIDAI_KYC_URL = config('UIDAI_KYC_URL', default="")
UIDAI_OTP_URL = config('UIDAI_OTP_URL', default="")
AUA_CODE = config('AUA_CODE', default="")
SUB_AUA_CODE = config('SUB_AUA_CODE', default="")
AUA_LICENSE_KEY = config('AUA_LICENSE_KEY', default="")
ASA_LICENSE_KEY = config('ASA_LICENSE_KEY', default="")
UIDAI_P12_PATH = config('UIDAI_P12_PATH', default="")
UIDAI_P12_PASS = config('UIDAI_P12_PASS', default="")

# ---------------------------------------------------
# CHANNELS (WEBSOCKETS)
# ---------------------------------------------------
ASGI_APPLICATION = "job_portal.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        # "BACKEND": "channels_redis.core.RedisChannelLayer",
        "BACKEND": "channels.layers.InMemoryChannelLayer",
        # "CONFIG": {
        #     "hosts": [("127.0.0.1", 6379)],
        # },
    },
}
