from django.contrib import admin

from video_app.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Upload and manage videos; conversion fields are read-only."""

    list_display = ['title', 'category', 'status', 'created_at']
    list_filter = ['category', 'status']
    search_fields = ['title']
    readonly_fields = ['status', 'thumbnail', 'created_at']

    def get_readonly_fields(self, request, obj=None):
        """Lock the video file after upload; a new file needs a new video."""
        if obj:
            return [*self.readonly_fields, 'video_file']
        return self.readonly_fields
