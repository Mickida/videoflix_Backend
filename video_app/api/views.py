from django.http import FileResponse, Http404
from django.views.static import serve
from rest_framework.response import Response
from rest_framework.views import APIView

from video_app.utils import (
    SEGMENT_PATTERN,
    IgnoreAcceptHeader,
    ensure_video_ready,
    get_thumbnail_dir,
    get_video_list_data,
    open_hls_file,
)


class VideoListView(APIView):
    """List all videos that are ready to stream."""

    throttle_scope = 'video'

    def get(self, request):
        """Return the cached list of ready videos."""
        return Response(get_video_list_data(request))


class HlsFileView(APIView):
    """Base view for HLS files; players send their own Accept header."""

    content_negotiation_class = IgnoreAcceptHeader
    throttle_scope = 'video'


class PlaylistView(HlsFileView):
    """Serve the HLS playlist of a video in one resolution."""

    def get(self, request, movie_id, resolution):
        """Return the index.m3u8 file."""
        file = open_hls_file(movie_id, resolution, 'index.m3u8')
        return FileResponse(file, content_type='application/vnd.apple.mpegurl')


class SegmentView(HlsFileView):
    """Serve a single HLS segment of a video in one resolution."""

    def get(self, request, movie_id, resolution, segment):
        """Return the .ts file if the segment name is valid."""
        if not SEGMENT_PATTERN.fullmatch(segment):
            raise Http404
        file = open_hls_file(movie_id, resolution, segment)
        return FileResponse(file, content_type='video/MP2T')


def thumbnail_view(request, video_id):
    """Serve the thumbnail of a ready video publicly; nothing else below /media/."""
    ensure_video_ready(video_id)
    return serve(request, f'{video_id}.jpg', document_root=get_thumbnail_dir())
