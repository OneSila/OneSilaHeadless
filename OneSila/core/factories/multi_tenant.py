from django.db import transaction
from django.core.exceptions import ValidationError


class InviteUserFactory:
    def __init__(self, data, model):
        self.data = data
        self.model = model

    @transaction.atomic
    def create_user(self):
        user = self.model(**self.data)

        try:
            user.full_clean()
        except ValidationError as e:
            if 'username' in str(e):
                raise Exception("Email is already taken.")

        user.save()
        self.user = user

    def send_invite(self):
        # FIXME: Send out (branded) email to the new user.
        pass

    def run(self):
        self.create_user()
        self.send_invite()
