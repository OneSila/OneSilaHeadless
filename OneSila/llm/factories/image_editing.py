from .mixins import ReplicateMixin
from django.conf import settings


class CutBackgroundBirefnet(ReplicateMixin):
    def __init__(self, image_url, save_to_filepath):
        super().__init__()
        self.image_url
        self.save_to_filepath = save_to_filepath

    def process_image(self):
        self.output = self.client.run(
            "men1scus/birefnet:f74986db0355b58403ed20963af156525e2891ea3c2d499bfbfb2a28cd87c5d7",
            input={
                "image": self.image_url,
                "resolution": ""
            }
        )
    
    def save_image(self):
        with open(self.save_to_filepath, 'wb') as f:
            f.write(self.output.read())

    def run(self):
        self.process_image()
        self.save_image()