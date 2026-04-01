from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.utils import timezone
from urllib.parse import urlencode
from datetime import timedelta

from premailer import transform
from collections import namedtuple
from get_absolute_url.helpers import generate_absolute_url
from integrations.constants import INTEGRATIONS_TYPES_MAP

import re

from .models import Notification


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


def build_product_tab_url(*, product, tab: str) -> str | None:
    if product is None or not getattr(product, "global_id", None):
        return None

    return _build_frontend_url(
        path=f"/products/product/{product.global_id}",
        query_params={"tab": tab},
    )


def build_sales_channel_tab_url(*, sales_channel, tab: str) -> str | None:
    if sales_channel is None:
        return None

    resolved = sales_channel.get_real_instance() if hasattr(sales_channel, "get_real_instance") else sales_channel
    global_id = getattr(resolved, "global_id", None)
    if not global_id:
        return None

    integration_type = INTEGRATIONS_TYPES_MAP.get(type(resolved))
    if not integration_type:
        return None

    return _build_frontend_url(
        path=f"/integrations/{integration_type}/{global_id}",
        query_params={"tab": tab},
    )


def build_import_tab_url(*, import_process) -> str | None:
    resolved = import_process.get_real_instance() if hasattr(import_process, "get_real_instance") else import_process
    sales_channel = getattr(resolved, "sales_channel", None)
    if sales_channel is None:
        return None

    return build_sales_channel_tab_url(sales_channel=sales_channel, tab="imports")


def create_user_notification(
    *,
    user,
    notification_type: str,
    title: str,
    message: str = "",
    url: str | None = None,
    metadata: dict | None = None,
    actor=None,
    multi_tenant_company=None,
):
    if user is None:
        return None

    cutoff = timezone.now() - timedelta(minutes=1)
    duplicate_exists = Notification.objects.filter(
        user=user,
        type=notification_type,
        created_by_multi_tenant_user=actor,
        title=title,
        message=message,
        url=url,
        created_at__gte=cutoff,
    ).exists()
    if duplicate_exists:
        return None

    return Notification.objects.create(
        multi_tenant_company=multi_tenant_company or getattr(user, "multi_tenant_company", None),
        created_by_multi_tenant_user=actor,
        last_update_by_multi_tenant_user=actor,
        user=user,
        type=notification_type,
        title=title,
        message=message,
        url=url,
        metadata=metadata or {},
    )


def _build_frontend_url(*, path: str, query_params: dict[str, str] | None = None) -> str:
    base_url = generate_absolute_url(trailing_slash=False).rstrip("/")
    normalized_path = path if path.startswith("/") else f"/{path}"
    if not query_params:
        return f"{base_url}{normalized_path}"

    return f"{base_url}{normalized_path}?{urlencode(query_params)}"
