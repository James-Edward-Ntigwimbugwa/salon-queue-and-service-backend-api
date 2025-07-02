from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
# configure swagger settings

schema_view = get_schema_view(
    openapi.Info(
        title="Salon Queue and Service API",
        default_version='v1',
        description="API documentation for the Salon Queue and Service application",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="jamesedwards2001.tz@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Authentication endpoints
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # App URLs
    path('api/accounts/', include('accounts.urls')),
    path('api/services/', include('services.urls')),
    path('api/order_queue/', include('order_queue.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reports/', include('reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)