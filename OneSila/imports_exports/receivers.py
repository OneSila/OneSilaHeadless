from core.receivers import receiver
from core.signals import post_create, post_update

# @receiver(post_update, sender='app_name.Model')
# def app_name__model__action__example(sender, instance, **kwargs):
#     do_something()