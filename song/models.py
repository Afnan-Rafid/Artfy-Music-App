from django.db import models
from django.utils.text import slugify


class Song(models.Model):
    title = models.CharField(max_length=100, blank=True)
    artist = models.CharField(max_length=100, blank=True)
    duration = models.DurationField(blank=True, null=True)
    cover_image = models.ImageField(upload_to='cover_images/', blank=True, null=True, default='cover_images/default-cover.jpg')
    audio_file = models.FileField(upload_to='audio_files/')
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return f"{self.title or 'Unknown Title'} by {self.artist or 'Unknown Artist'}"

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            slug = base_slug
            count = 1
            # Ensure slug uniqueness
            while Song.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)