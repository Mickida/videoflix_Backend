from functools import partial

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from video_app.models import Video
from video_app.tasks import queue_conversion
from video_app.utils import clear_video_list_cache, delete_video_files


@receiver([post_save, post_delete], sender=Video)
def clear_cache_on_change(sender, **kwargs):
    """Drop the cached video list once a change of a video is committed."""
    transaction.on_commit(clear_video_list_cache)


@receiver(post_save, sender=Video)
def queue_video_conversion(sender, instance, created, **kwargs):
    """Queue the HLS conversion once a new video is saved."""
    if created:
        transaction.on_commit(partial(queue_conversion, instance.id))


@receiver(post_delete, sender=Video)
def remove_video_files(sender, instance, **kwargs):
    """Delete all files of a video once its deletion is committed."""
    # Pass the id now: Django sets instance.id to None after the delete.
    transaction.on_commit(partial(delete_video_files, instance, instance.id))
