import re
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.http import Http404

from video_app.api.serializers import VideoSerializer
from video_app.models import Video

RESOLUTIONS = {'480p': 480, '720p': 720, '1080p': 1080}
SEGMENT_SECONDS = 6
# At least three digits: FFmpeg names segment 1000 "1000.ts". ASCII only, used with fullmatch.
SEGMENT_PATTERN = re.compile(r'\d{3,}\.ts', re.ASCII)
VIDEO_LIST_CACHE_KEY = 'video_list'
VIDEO_LIST_CACHE_SECONDS = 60 * 15


def get_hls_dir(video_id):
    """Return the folder that holds all HLS files of a video."""
    return Path(settings.MEDIA_ROOT) / 'hls' / str(video_id)


def get_thumbnail_dir():
    """Return the only media folder that is served publicly."""
    return Path(settings.MEDIA_ROOT) / 'thumbnails'


def get_thumbnail_name(video_id):
    """Return the storage name of a video's thumbnail."""
    return f'thumbnails/{video_id}.jpg'


def get_video_list_data(request):
    """Return the ready videos with absolute thumbnail URLs for this request."""
    data = cache.get(VIDEO_LIST_CACHE_KEY)
    if data is None:
        videos = Video.objects.filter(status=Video.Status.READY)
        data = list(VideoSerializer(videos, many=True).data)
        cache.set(VIDEO_LIST_CACHE_KEY, data, VIDEO_LIST_CACHE_SECONDS)
    return make_thumbnail_urls_absolute(data, request)


def make_thumbnail_urls_absolute(data, request):
    """Prefix the cached relative thumbnail paths with the host of this request."""
    return [
        {**item, 'thumbnail_url': item['thumbnail_url'] and request.build_absolute_uri(item['thumbnail_url'])}
        for item in data
    ]


def clear_video_list_cache():
    """Drop the cached video list, so the next request rebuilds it."""
    cache.delete(VIDEO_LIST_CACHE_KEY)


def ensure_video_ready(video_id):
    """Raise Http404 unless the video exists and is ready to stream."""
    if not Video.objects.filter(id=video_id, status=Video.Status.READY).exists():
        raise Http404


def open_hls_file(movie_id, resolution, file_name):
    """Open an HLS file of a ready video for reading or raise Http404."""
    if resolution not in RESOLUTIONS:
        raise Http404
    ensure_video_ready(movie_id)
    try:
        return (get_hls_dir(movie_id) / resolution / file_name).open('rb')
    except OSError:  # Missing, a folder, or deleted in the meantime.
        raise Http404 from None


def build_thumbnail_command(source, target):
    """Return the FFmpeg arguments for a still image after one second."""
    return [
        'ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-ss', '1', '-i', str(source),
        '-frames:v', '1', '-vf', 'scale=640:-2', str(target),
    ]


def build_hls_command(source, target_dir, height):
    """Return the FFmpeg arguments for one HLS stream with the given height."""
    return [
        'ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', str(source),
        '-vf', f'scale=-2:{height}', '-c:v', 'libx264', '-preset', 'veryfast',
        # 8-bit 4:2:0 plays in every browser; subtitle tracks are dropped.
        '-crf', '23', '-pix_fmt', 'yuv420p', '-sn',
        # Keyframes every segment length, so FFmpeg can cut exact segments.
        '-force_key_frames', f'expr:gte(t,n_forced*{SEGMENT_SECONDS})',
        '-c:a', 'aac', '-b:a', '128k',
        '-hls_time', str(SEGMENT_SECONDS), '-hls_playlist_type', 'vod',
        '-hls_segment_filename', str(target_dir / '%03d.ts'),
        str(target_dir / 'index.m3u8'),
    ]


def run_ffmpeg(command):
    """Run an FFmpeg command and raise CalledProcessError if it fails."""
    subprocess.run(command, check=True, capture_output=True, text=True)


def delete_video_files(video, video_id):
    """Delete the original, the thumbnail and the HLS folder of a video."""
    video.video_file.delete(save=False)
    video.thumbnail.delete(save=False)
    # Also by name, because the instance may predate the thumbnail.
    (Path(settings.MEDIA_ROOT) / get_thumbnail_name(video_id)).unlink(missing_ok=True)
    shutil.rmtree(get_hls_dir(video_id), ignore_errors=True)
