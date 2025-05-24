from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('music/<slug:slug>', views.music, name='music'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('upload/', views.upload, name='upload'),
    path('download/', views.download_youtube_song, name='download'),
    path('library/', views.library, name='library'),
    path('delete/<slug:slug>/', views.delete, name='delete'),

]
