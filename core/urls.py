from django.contrib import admin
from django.urls import include, path, re_path

from video_app.api.views import thumbnail_view

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^media/thumbnails/(?P<video_id>[0-9]+)\.jpg$', thumbnail_view),
    path('django-rq/', include('django_rq.urls')),
    path('api/', include('auth_app.api.urls')),
    path('api/', include('video_app.api.urls')),
]
