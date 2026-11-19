import logging
import shutil
from pathlib import Path

import django_rq
from django.conf import settings
from redis.exceptions import RedisError

from video_app.models import Video
from video_app.tasks import convert_video

logger = logging.getLogger(__name__)


def get_hls_dir(video_id):
    """Return the folder that holds all HLS files of a video."""
    return Path(settings.MEDIA_ROOT) / 'hls' / str(video_id)


def queue_conversion(video_id):
    """Queue the conversion job; mark the video as failed if Redis is down."""
    try:
        django_rq.enqueue(convert_video, video_id)
    except RedisError:
        logger.exception('Could not queue the conversion of video %s.', video_id)
        Video.objects.filter(id=video_id).update(status=Video.Status.FAILED)


def delete_video_files(video, video_id):
    """Delete the original, the thumbnail and the HLS folder of a video."""
    video.video_file.delete(save=False)
    video.thumbnail.delete(save=False)
    shutil.rmtree(get_hls_dir(video_id), ignore_errors=True)
