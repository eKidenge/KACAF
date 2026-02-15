from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from accounts import views as accounts_views
from programs import views as programs_views
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# -------------------------------
# Root redirect based on authentication
# -------------------------------
def root_redirect(request):
    """
    Redirect based on authentication:
    - Superuser/staff -> admin dashboard
    - Executive -> executive dashboard
    - Member -> member dashboard
    - Anonymous -> public home
    """
    #if request.user.is_authenticated:
    #    if request.user.is_superuser or request.user.is_staff:
     #       return HttpResponseRedirect('/dashboard/admin/')
      #  elif getattr(request.user, "user_type", None) == 'executive':
     #       return HttpResponseRedirect('/dashboard/executive/')
     #   elif getattr(request.user, "user_type", None) == 'member':
     #       return HttpResponseRedirect('/dashboard/member/')
    return HttpResponseRedirect('/home/')


# -------------------------------
# API documentation schema
# -------------------------------
schema_view = get_schema_view(
    openapi.Info(
        title="KACAF API",
        default_version='v1',
        description="KACAF API documentation with JWT authentication and role-based access.",
        terms_of_service="https://kacaf.org/terms/",
        contact=openapi.Contact(email="api@kacaf.org"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


# -------------------------------
# URL patterns
# -------------------------------
urlpatterns = [
    # Root redirect
    path("", root_redirect, name="root"),

    # Accounts app handles home and dashboards
    #path("home/", accounts_views.public_dashboard, name="public_home"),  # <-- THIS fixes /home/
    path("home/", programs_views.public_dashboard, name="public_home"),

    path("accounts/", include("accounts.urls", namespace="accounts")),


    # Admin
    path("admin/", admin.site.urls),

    # JWT auth
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # App APIs
    #path("api/accounts/", include("accounts.urls")),
    path("api/governance/", include("governance.urls")),
    #path("api/programs/", include("programs.urls")),
    #path("programs/", include("programs.urls")),  # Handles both web and API
    path("programs/", include(("programs.urls", "programs"), namespace="programs")),
    path("api/programs/", include(("programs.urls", "programs_api"), namespace="programs_api")),

    path("api/finance/", include("finance.urls")),
    path("api/events/", include("events.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/communications/", include("communications.urls")),
    path("about/", TemplateView.as_view(template_name="base/about.html"), name="about"),

    # Add this with the other app URLs
    path("resources/", include(("resources.urls", "resources"), namespace="resources")),
    path("api/resources/", include(("resources.urls", "resources_api"), namespace="resources_api")),
    path('terms/', TemplateView.as_view(template_name='terms_of_service.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='privacy_policy.html'), name='privacy_policy'),
    path('privacy/', TemplateView.as_view(template_name='privacy_policy.html'), name='privacy-policy'),

    # API Docs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # DRF browsable API login
    path("api-auth/", include("rest_framework.urls")),

    # Health check
    path("health/", include("health_check.urls")),
]


# -------------------------------
# Admin site customization
# -------------------------------
admin.site.site_header = "KACAF Administration"
admin.site.site_title = "KACAF Admin Portal"
admin.site.index_title = "Welcome to KACAF Administration"


# -------------------------------
# Static & media (dev only)
# -------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
