from django.core.validators import FileExtensionValidator
from django.db import models

VIDEO_EXTENSIONS = ['mp4', 'mov', 'mkv', 'webm', 'avi']


class Video(models.Model):
    """A video that is uploaded in the admin and streamed as HLS."""

    class Category(models.TextChoices):
        """Genres the dashboard groups the videos by."""

        ACTION = 'Action'
        COMEDY = 'Comedy'
        DOCUMENTARY = 'Documentary'
        DRAMA = 'Drama'
        HORROR = 'Horror'
        ROMANCE = 'Romance'
        SCI_FI = 'Sci-Fi', 'Sci-Fi'

    class Status(models.TextChoices):
        """Steps of the HLS conversion."""

        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=Category.choices)
    video_file = models.FileField(
        upload_to='videos/',
        validators=[FileExtensionValidator(VIDEO_EXTENSIONS)],
    )
    thumbnail = models.FileField(upload_to='thumbnails/', blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Newest videos first."""

        ordering = ['-created_at']

    def __str__(self):
        """Return the title for the admin."""
        return self.title
