from core.exceptions import SoftSanityCheckError

import os


class PopulateTitleFactory:
    def __init__(self, media_instance, save=True):
        self.media_instance = media_instance
        self.save = save

    def sanity_check(self):
        if self.media_instance.title:
            raise SoftSanityCheckError(f"Media instance {self.media_instance.id} already has a title")

    def set_path(self):
        if self.media_instance.type == self.media_instance.IMAGE and self.media_instance.image:
            self.path = self.media_instance.image.path
        elif self.media_instance.type == self.media_instance.FILE and self.media_instance.file:
            self.path = self.media_instance.file.path
        elif self.media_instance.type == self.media_instance.VIDEO and self.media_instance.video_url:
            self.path = self.media_instance.video_url
        else:
            raise ValueError(f"Media instance {self.media_instance.type} not supported")

    def set_filename(self):
        self.filename = os.path.basename(self.path)

    def set_title(self):
        self.title = os.path.splitext(self.filename)[0]

    def update_instance(self):
        self.media_instance.title = self.title
        
        if self.save:
            self.media_instance.save(update_fields=['title'])

    def run(self):
        self.sanity_check()
        self.set_path()
        self.set_filename()
        self.set_title()
        self.update_instance()