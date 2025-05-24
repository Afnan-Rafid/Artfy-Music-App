from django.contrib import admin
from .models import Song

# Register your models here.

class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'duration', 'slug')
    search_fields = ('title', 'artist')
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(Song, SongAdmin)

