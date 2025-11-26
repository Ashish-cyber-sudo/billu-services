from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# This view handles requests from Chrome DevTools without breaking the app
def chrome_devtools_ignore(request):
    return JsonResponse({}, status=204)

urlpatterns = [
    path(".well-known/appspecific/com.chrome.devtools.json", chrome_devtools_ignore),
    path("admin/", admin.site.urls),
    path("", include("job_app.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
