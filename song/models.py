from django.db import models
from django.utils.text import slugify


class Song(models.Model):
    title = models.CharField(max_length=100, blank=True)
    artist = models.CharField(max_length=100, blank=True)
    duration = models.DurationField(blank=True, null=True)
    
    # Cloudinary paths will auto-handle folders by prefix
    cover_image = models.URLField(blank=True, null=True)
    audio_file = models.URLField()
    
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return f"{self.title or 'Unknown Title'} by {self.artist or 'Unknown Artist'}"

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            slug = base_slug
            count = 1
            # Ensure slug is unique
            while Song.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)