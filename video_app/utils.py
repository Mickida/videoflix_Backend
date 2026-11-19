import shutil
import subprocess
from pathlib import Path

from django.conf import settings

RESOLUTIONS = {'480p': 480, '720p': 720, '1080p': 1080}
SEGMENT_SECONDS = 6


def get_hls_dir(video_id):
    """Return the folder that holds all HLS files of a video."""
    return Path(settings.MEDIA_ROOT) / 'hls' / str(video_id)


def get_thumbnail_name(video_id):
    """Return the storage name of a video's thumbnail."""
    return f'thumbnails/{video_id}.jpg'


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
