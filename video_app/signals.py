from functools import partial

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from video_app.models import Video
from video_app.utils import delete_video_files, queue_conversion


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
