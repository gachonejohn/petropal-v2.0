from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('acc/api/auth/', include('accounts.urls')),
    path('api/v1/', include('profiles.urls')),
    path('api/v1.0/', include('posts.urls')),
    path('api/v1.1/', include('chat.urls')),
    path('api/v1.2/', include('news_room.urls')),
    path('api/v1.3/', include('ad_events.urls')),
    path('api/v1.4/', include('report.urls')),
] 
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

