from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string

from premailer import transform
from collections import namedtuple
from get_absolute_url.helpers import generate_absolute_url

import re


EmailAttachment = namedtuple('EmailAttachment', 'name, content')


def textify(html):
    # Remove html tags and continuous whitespaces
    text_only = re.sub('[ \t]+', ' ', strip_tags(html))
    # Strip single spaces in the beginning of each line
    return text_only.replace('\n ', '\n').strip()


def send_branded_mail(subject, html, to_email, from_email=None, fail_silently=True, attachment=None, **kwargs):
    '''
    Send a branded email with all signatures in place.
    '''

    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL

    text = textify(html)
    html = transform(html, base_url=generate_absolute_url())

    mail = EmailMultiAlternatives(subject, text, from_email, [to_email])
    mail.attach_alternative(html, "text/html")

    if attachment:
        if not isinstance(attachment, EmailAttachment):
            raise ValueError(f'Attachment should be an EmailAttachment instance, not {type(attachment)}')

        extension = attachment.name.split('.')[-1]

        if extension in ['xlsx']:
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif extension in ['pdf']:
            content_type = 'application/pdf'
        else:
            raise ValueError('Unkown content type.')

        mail.attach(attachment.name, attachment.content, content_type)

    # Lets override fail_silently for dev-env
    if settings.DEBUG:
        fail_silently = False

    return mail.send(fail_silently=fail_silently)

    # return send_mail(subject, text, from_email, [to_email], html_message=html, fail_silently=fail_silently, **kwargs)
