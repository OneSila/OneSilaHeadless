from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from strawberry.relay import GlobalID
from strawberry.types import Info

from core.schema.core.helpers import get_multi_tenant_company, get_current_user
from notifications.models import CollaborationThread


def resolve_collaboration_target(*, info: Info, target_id: GlobalID):
    target = target_id.resolve_node_sync(info, required=True)
    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

    target_company_id = getattr(target, "multi_tenant_company_id", None)
    if target_company_id is None:
        raise ValidationError("This object cannot be used for collaboration.")

    if target_company_id != multi_tenant_company.id:
        raise PermissionDenied("Invalid company")

    return target


def get_target_content_type(*, target):
    return ContentType.objects.get_for_model(target, for_concrete_model=False)


def build_thread_default_url(*, target, explicit_url: str | None = None) -> str | None:
    if explicit_url:
        return explicit_url

    get_absolute_url = getattr(target, "get_absolute_url", None)
    if callable(get_absolute_url):
        return get_absolute_url()

    return None


def get_collaboration_thread(*, info: Info, target_id: GlobalID) -> CollaborationThread | None:
    target = resolve_collaboration_target(info=info, target_id=target_id)
    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
    content_type = get_target_content_type(target=target)

    return CollaborationThread.objects.filter(
        multi_tenant_company=multi_tenant_company,
        content_type=content_type,
        object_id=target.pk,
    ).first()


def get_or_create_collaboration_thread(*, info: Info, target_id: GlobalID, url: str | None = None) -> tuple[CollaborationThread, bool]:
    target = resolve_collaboration_target(info=info, target_id=target_id)
    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
    current_user = get_current_user(info)
    content_type = get_target_content_type(target=target)

    thread, created = CollaborationThread.objects.get_or_create(
        multi_tenant_company=multi_tenant_company,
        content_type=content_type,
        object_id=target.pk,
        defaults={
            "url": build_thread_default_url(target=target, explicit_url=url),
            "created_by_multi_tenant_user": current_user,
            "last_update_by_multi_tenant_user": current_user,
        },
    )

    if not created:
        updated = False
        if url and thread.url != url:
            thread.url = url
            updated = True
        if thread.last_update_by_multi_tenant_user_id != current_user.id:
            thread.last_update_by_multi_tenant_user = current_user
            updated = True
        if updated:
            thread.save()

    return thread, created
