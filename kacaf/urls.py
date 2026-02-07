from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

# API Documentation imports
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Schema view for API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="KACAF API",
        default_version='v1',
        description="""
        Kenya Agroforestry and Climate Action Foundation (KACAF) API Documentation.
        
        This API provides endpoints for managing:
        - User accounts and authentication
        - Governance and organizational structure
        - Programs and projects
        - Financial management
        - Events and registrations
        - Documents and resources
        - Communications and announcements
        
        ### Authentication
        This API uses JWT (JSON Web Token) for authentication.
        1. Obtain tokens at `/api/auth/token/`
        2. Include token in header: `Authorization: Bearer <access_token>`
        
        ### User Roles
        - **Chairperson**: Full administrative rights
        - **Executive Committee**: Extended permissions
        - **Members**: Regular authenticated users
        - **Staff**: Administrative staff
        - **Donors/Partners**: Limited access
        
        ### Rate Limiting
        - Anonymous: 100 requests/hour
        - Authenticated: 1000 requests/hour
        - Staff/Executive: 5000 requests/hour
        """,
        terms_of_service="https://kacaf.org/terms/",
        contact=openapi.Contact(email="api@kacaf.org"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    path('', include('pages.urls', namespace='pages')),  # Pages app
    
    # API Authentication URLs
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # App URLs
    path('api/accounts/', include('accounts.urls')),
    path('api/governance/', include('governance.urls')),
    path('api/programs/', include('programs.urls')),
    path('api/finance/', include('finance.urls')),
    path('api/events/', include('events.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/communications/', include('communications.urls')),
    
    # API Documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), 
            name='schema-json'),
    path('swagger/', 
         schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', 
         schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),
    
    # Django REST Framework authentication URLs
    path('api-auth/', include('rest_framework.urls')),
    
    # Health check endpoint
    path('health/', include('health_check.urls')),
]

# Admin site customization
admin.site.site_header = "KACAF Administration"
admin.site.site_title = "KACAF Admin Portal"
admin.site.index_title = "Welcome to KACAF Administration"

# Only serve static/media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar (if installed)
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns