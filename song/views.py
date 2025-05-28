from django.shortcuts import render, redirect
from .models import Song
from django.utils.text import slugify
from datetime import timedelta
from django.shortcuts import get_object_or_404
import os
import uuid
from yt_dlp import YoutubeDL
from django.conf import settings
import requests
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from cloudinary.uploader import upload as cloudinary_upload
from cloudinary.utils import cloudinary_url
# Create your views here.

def index(request):
    return render(request, 'base.html')
@login_required
def home(request):
    query = request.GET.get('q')
    if query:
        songs = Song.objects.filter(
            Q(title__icontains=query) | Q(artist__icontains=query)
        )
    else:
        songs = Song.objects.all()

    return render(request, 'index.html', {'songs': songs})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('login')

@login_required
def library(request):
    query = request.GET.get('q')
    if query:
        songs = Song.objects.filter(
            Q(title__icontains=query) | Q(artist__icontains=query)
        )
    else:
        songs = Song.objects.all()

    return render(request, 'library.html', {'songs': songs})

@login_required
def music(request, slug):

    songs = list(Song.objects.all().order_by('id'))


    current_song = get_object_or_404(Song, slug=slug)

    try:
        current_index = songs.index(current_song)
    except ValueError:
        current_index = 0

   
    prev_song = songs[current_index - 1] if current_index > 0 else songs[-1]
    next_song = songs[current_index + 1] if current_index < len(songs) - 1 else songs[0]

    context = {
        'song': current_song,
        'prev_song': prev_song,
        'next_song': next_song,
    }
    return render(request, 'music.html', context)

@login_required
def upload(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        artist = request.POST.get('artist')
        duration_str = request.POST.get('duration')
        cover_image_file = request.FILES.get('cover_image')
        audio_file_file = request.FILES.get('audio_file')

        duration = None
        if duration_str:
            try:
                mins, secs = map(int, duration_str.split(':'))
                duration = timedelta(minutes=mins, seconds=secs)
            except:
                duration = None

        # Upload to Cloudinary
        cover_image_url = None
        if cover_image_file:
            cover_upload = cloudinary_upload(cover_image_file, folder="cover_images")
            cover_image_url = cover_upload['secure_url']

        audio_upload = cloudinary_upload(audio_file_file, resource_type="video", folder="audio_files")
        audio_file_url = audio_upload['secure_url']

        song = Song.objects.create(
            title=title,
            artist=artist,
            duration=duration,
            cover_image=cover_image_url,
            audio_file=audio_file_url,
        )
        return redirect('home')

    return render(request, 'upload.html')




@login_required
def download_youtube_song(request):
    if request.method == "POST":
        youtube_url = request.POST.get('youtube_url')

        if not youtube_url:
            return render(request, 'download.html', {'error': 'Please enter a YouTube URL.'})

        try:
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)

            songs_dir = os.path.join(settings.MEDIA_ROOT, 'songs')
            os.makedirs(songs_dir, exist_ok=True)

            cover_dir = os.path.join(settings.MEDIA_ROOT, 'cover_images')
            os.makedirs(cover_dir, exist_ok=True)

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s-%(id)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                title = info_dict.get('title', 'unknown_title')
                artist = info_dict.get('uploader', 'unknown_artist')
                video_id = info_dict.get('id')
                duration_seconds = info_dict.get('duration')
                duration = timedelta(seconds=duration_seconds) if duration_seconds else None

            slug = generate_unique_slug(title)

            # ---------------- Cover Image from Thumbnail ----------------
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            response = requests.get(thumbnail_url)
            if response.status_code != 200:
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                response = requests.get(thumbnail_url)

            cover_filename = f"{slug}-{uuid.uuid4()}.jpg"
            cover_path = os.path.join('cover_images', cover_filename)
            full_cover_path = os.path.join(settings.MEDIA_ROOT, cover_path)
            with open(full_cover_path, 'wb') as f:
                f.write(response.content)

            # ---------------- Audio File Handling ----------------
            mp3_temp_path = os.path.join(temp_dir, f"{slug}-{info_dict['id']}.mp3")
            if not os.path.exists(mp3_temp_path):
                files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
                if files:
                    mp3_temp_path = os.path.join(temp_dir, files[0])
                else:
                    raise Exception("MP3 file not found after download.")

            mp3_filename = f"{slug}-{uuid.uuid4()}.mp3"
            mp3_final_path = os.path.join(songs_dir, mp3_filename)
            os.rename(mp3_temp_path, mp3_final_path)

            with open(full_cover_path, 'rb') as f:
                cover_upload = cloudinary_upload(f, folder="cover_images")
            cover_image_url = cover_upload['secure_url']

            # Upload MP3 to Cloudinary
            with open(mp3_final_path, 'rb') as f:
                audio_upload = cloudinary_upload(f, resource_type="video", folder="audio_files")
            audio_file_url = audio_upload['secure_url']


            # ---------------- Save Song ----------------
            song = Song.objects.create(
                title=title,
                artist=artist,
                audio_file=audio_file_url,
                cover_image=cover_image_url,
                slug=slug,
                duration=duration,
            )

            return redirect('music', slug=song.slug)

        except Exception as e:
            return render(request, 'download.html', {'error': f'Error: {str(e)}'})

    return render(request, 'download.html')


def generate_unique_slug(title):
    base_slug = slugify(title)
    slug = base_slug
    num = 1
    from .models import Song
    while Song.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{num}"
        num += 1
    return slug
@login_required
def delete(request, slug):
    song = get_object_or_404(Song, slug=slug)
    song.audio_file.delete(save=False) 
    song.delete()
    return redirect('home')  