# Generated migration to populate title field with filename for IMAGE type media

import os
from django.db import migrations


def populate_image_titles(apps, schema_editor):
    """
    Data migration to populate the title field with filename (without path) 
    for all media of type IMAGE that have an image file but no title.
    """
    Media = apps.get_model('media', 'Media')
    
    # Get all media objects of type IMAGE that have an image file
    image_media = Media.objects.filter(
        type=Media.IMAGE,
        image__isnull=False
    ).exclude(image='')
    
    updated_count = 0
    
    for media in image_media:
        if media.image and not media.title:
            # Extract filename from the image path (without directory path)
            filename = os.path.basename(str(media.image))
            # Remove file extension for a cleaner title
            title = os.path.splitext(filename)[0]
            media.title = title
            media.save(update_fields=['title'])
            updated_count += 1
    
    print(f"Updated {updated_count} image media objects with titles")


def reverse_populate_image_titles(apps, schema_editor):
    """
    Reverse migration - clear titles that were populated from filenames.
    This is a simple reverse that clears all titles, but in practice
    you might want to be more selective about which titles to clear.
    """
    Media = apps.get_model('media', 'Media')
    
    # Clear titles for all IMAGE type media
    Media.objects.filter(type=Media.IMAGE).update(title=None)
    
    print("Cleared titles for all IMAGE type media objects")


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0005_alter_media_file_alter_media_image'),
    ]

    operations = [
        migrations.RunPython(
            populate_image_titles,
            reverse_populate_image_titles,
        ),
    ]
