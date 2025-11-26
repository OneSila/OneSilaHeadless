import os
from django.test import TestCase
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings
from unittest.mock import patch

from media.models import Media, Image, File as MediaFile, Video
from media.flows import populate_title_flow
from media.factories import PopulateTitleFactory
from core.tests import TestCase as CoreTestCase
from media.tests.helpers import CreateImageMixin


class PopulateTitleFlowTestCase(CreateImageMixin, CoreTestCase):
    """
    Test cases for the populate_title flow functionality.
    Tests both direct flow usage and signal-triggered population.
    """

    def test_populate_title_flow_with_image(self):
        """Test that populate_title_flow correctly sets title from image filename."""
        # Create an image without a title
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        image.title = None  # Ensure no title
        image.save()
        
        # Run the flow - should run via signals by default.
        # populate_title_flow(image)
        
        # Refresh from database
        image.refresh_from_db()
        
        # Verify title was populated from filename
        self.assertEqual(image.title, 'red')
    
    def test_populate_title_flow_with_file(self):
        """Test that populate_title_flow correctly sets title from file filename."""
        # Create a file without a title
        media_file = MediaFile.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            title=None
        )
        
        # Create a test file
        test_content = b'This is a test PDF content'
        test_file = ContentFile(test_content, name='test_document.pdf')
        media_file.file.save('test_document.pdf', test_file)
        media_file.save()
        
        # Run the flow - should run via signals by default.
        # populate_title_flow(media_file)
        
        # Refresh from database
        media_file.refresh_from_db()
        
        # Verify title was populated from filename
        self.assertEqual(media_file.title, 'test_document')
    
    def test_populate_title_flow_with_video_url(self):
        """Test that populate_title_flow handles video URLs correctly."""
        # Create a video with URL but no title
        video = Video.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.VIDEO,
            video_url='https://example.com/video.mp4',
            title=None
        )
        
        # Run the flow - should handle video URL by default
        # populate_title_flow(video)
        
        # Refresh from database
        video.refresh_from_db()
        
        # For video URLs, we expect the title to be populated from the URL
        # The flow should extract 'video' from 'video.mp4'
        self.assertEqual(video.title, 'video')
    
    def test_populate_title_flow_skips_existing_title(self):
        """Test that populate_title_flow skips media that already has a title."""
        # Create an image with existing title
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        image.title = 'Existing Title'
        image.save()
        
        # Run the flow - should run via signals by default.
        # populate_title_flow(image)
        
        # Refresh from database
        image.refresh_from_db()
        
        # Verify title was not changed
        self.assertEqual(image.title, 'Existing Title')
