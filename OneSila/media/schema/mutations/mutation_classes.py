from strawberry_django.optimizer import DjangoOptimizerExtension

from core.schema.core.mixins import GetCurrentUserMixin
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import type, CreateMutation
from media.models import Video, Media, Image, File


class CreateWithOwnerMutation(CreateMutation, GetCurrentUserMixin):
    """
    Every create needs to include the company a user is assigned to.
    """

    def create(self, data: dict[str, Any], *, info: Info):
        user = self.get_current_user(info, fail_silently=False)
        data['owner'] = user
        map = {
            Video: Media.VIDEO,
            Image: Media.IMAGE,
            File: Media.FILE,
        }
        data['type'] = map.get(self.django_model, None)

        return super().create(data=data, info=info)
