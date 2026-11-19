from django.urls import path

from video_app.api.views import PlaylistView, SegmentView, VideoListView

# The playlist route must stay above the segment routes.
urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path(
        'video/<int:movie_id>/<str:resolution>/index.m3u8',
        PlaylistView.as_view(), name='video-playlist',
    ),
    # HLS.js requests segments without a trailing slash, the docs show one.
    path(
        'video/<int:movie_id>/<str:resolution>/<str:segment>',
        SegmentView.as_view(), name='video-segment',
    ),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>/', SegmentView.as_view()),
]
