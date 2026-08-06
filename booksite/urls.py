from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from booksite_functions.views import health_check


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/", include("booksite_functions.api_urls")),
    path("", include(("booksite_functions.urls", "books"))),
    path('account/', include("allauth.urls")),
    path('health/', health_check, name='health-check'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
        path('sentry-debug/', trigger_error),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)