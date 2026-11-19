import logging
import subprocess
from pathlib import Path

import django_rq
from django.conf import settings
from redis.exceptions import RedisError

from video_app.models import Video
from video_app.utils import (
    RESOLUTIONS,
    build_hls_command,
    build_thumbnail_command,
    clear_video_list_cache,
    get_hls_dir,
    get_thumbnail_name,
    run_ffmpeg,
)

logger = logging.getLogger(__name__)

MAX_LOGGED_STDERR = 2000


def queue_conversion(video_id):
    """Queue the conversion job; mark the video as failed if Redis is down."""
    try:
        django_rq.enqueue(convert_video, video_id)
    except RedisError:
        logger.exception('Could not queue the conversion of video %s.', video_id)
        Video.objects.filter(id=video_id).update(status=Video.Status.FAILED)


def convert_video(video_id):
    """Convert an uploaded video into a thumbnail and HLS streams."""
    video = Video.objects.filter(id=video_id, status=Video.Status.PENDING).first()
    if video is None:
        return
    set_status(video_id, Video.Status.PROCESSING)
    try:
        create_thumbnail(video)
        create_hls_streams(video)
    except subprocess.CalledProcessError as error:
        logger.error('FFmpeg failed for video %s: %s', video_id, error.stderr[-MAX_LOGGED_STDERR:])
        set_status(video_id, Video.Status.FAILED)
        return
    except Exception:
        # Also covers the RQ job timeout; re-raise so RQ lists the job as failed.
        logger.exception('Conversion of video %s crashed.', video_id)
        set_status(video_id, Video.Status.FAILED)
        raise
    set_status(video_id, Video.Status.READY)


def set_status(video_id, status):
    """Save a new conversion status; does nothing if the video is gone."""
    Video.objects.filter(id=video_id).update(status=status)
    # update() sends no post_save signal, so the cache is cleared here.
    clear_video_list_cache()


def create_thumbnail(video):
    """Create the thumbnail image and store its path on the video."""
    name = get_thumbnail_name(video.id)
    target = Path(settings.MEDIA_ROOT) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(build_thumbnail_command(video.video_file.path, target))
    Video.objects.filter(id=video.id).update(thumbnail=name)


def create_hls_streams(video):
    """Create one HLS stream for every supported resolution."""
    for resolution, height in RESOLUTIONS.items():
        target_dir = get_hls_dir(video.id) / resolution
        target_dir.mkdir(parents=True, exist_ok=True)
        run_ffmpeg(build_hls_command(video.video_file.path, target_dir, height))
