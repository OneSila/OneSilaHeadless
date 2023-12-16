from django.urls import path
from .views import ImageListView, ImageDetailViev, ImageUpdateView, ImageDeleteView, \
    MediaListView, MediaDetailViev, MediaUpdateView, MediaDeleteView, \
    VideoListView, VideoDetailViev, VideoUpdateView, VideoDeleteView


app_name = 'media'

urlpatterns = [
    path('images/', ImageListView.as_view(), name='images_list'),
    path('images/<str:pk>/', ImageDetailViev.as_view(), name='image_detail'),
    path('images/<str:pk>/update/', ImageUpdateView.as_view(), name='image_update'),
    path('images/<str:pk>/delete/', ImageDeleteView.as_view(), name='image_delete'),
    path('medias/', MediaListView.as_view(), name='medias_list'),
    path('medias/<str:pk>/', MediaDetailViev.as_view(), name='media_detail'),
    path('medias/<str:pk>/update/', MediaUpdateView.as_view(), name='media_update'),
    path('medias/<str:pk>/delete/', MediaDeleteView.as_view(), name='media_delete'),
    path('videos/', VideoListView.as_view(), name='videos_list'),
    path('videos/<str:pk>/', VideoDetailViev.as_view(), name='video_detail'),
    path('videos/<str:pk>/update/', VideoUpdateView.as_view(), name='video_update'),
    path('videos/<str:pk>/delete/', VideoDeleteView.as_view(), name='video_delete'),
]
