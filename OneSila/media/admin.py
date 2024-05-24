from django.contrib import admin

from media.models import Media


# Register your models here.
@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    pass
