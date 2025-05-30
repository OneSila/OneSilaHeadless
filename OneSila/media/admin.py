from django.contrib import admin
from core.admin import ModelAdmin
from media.models import Media, MediaProductThrough


@admin.register(Media)
class MediaAdmin(ModelAdmin):
    pass


@admin.register(MediaProductThrough)
class MediaProductThroughAdmin(ModelAdmin):
    pass
