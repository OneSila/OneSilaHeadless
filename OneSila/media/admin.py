from django.contrib import admin

from media.models import Media, MediaProductThrough

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    pass

@admin.register(MediaProductThrough)
class MediaProductThroughAdmin(admin.ModelAdmin):
    pass