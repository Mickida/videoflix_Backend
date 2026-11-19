from rest_framework import serializers

from video_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    """Video data for the dashboard, with a relative thumbnail path."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']

    def get_thumbnail_url(self, video):
        """Return the thumbnail path; the view makes it absolute per request."""
        if not video.thumbnail:
            return None
        return video.thumbnail.url
