from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    name = 'video_app'

    def ready(self):
        """Register the signal handlers."""
        import video_app.signals  # noqa: F401
