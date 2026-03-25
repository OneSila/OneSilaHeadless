from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views import View

from core.views import EmptyTemplateView
from .models import IntegrationTaskQueue, PublicIntegrationType
from .helpers import get_public_integration_asset_url


@login_required
@user_passes_test(lambda u: u.is_superuser)
def retry_integration_task(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(IntegrationTaskQueue, id=task_id)
        task.retry_task(retry_now=True)
        messages.success(request, f"Task {task.name} has been retried.")
    else:
        return HttpResponseForbidden("Invalid request method.")

    return redirect(request.META.get('HTTP_REFERER', '/'))


class IntegrationListView(EmptyTemplateView):
    pass


class ShopifyIntegrationDetailView(EmptyTemplateView):
    pass


class AmazonIntegrationDetailView(EmptyTemplateView):
    pass


class PublicIntegrationTypeDirectListView(View):
    BOOLEAN_FILTERS = {
        "active": "active",
        "is_beta": "is_beta",
        "supports_open_ai_product_feed": "supports_open_ai_product_feed",
    }
    EXACT_FILTERS = {
        "key": "key",
        "type": "type",
        "subtype": "subtype",
        "category": "category",
        "based_to_key": "based_to__key",
    }
    INTEGER_FILTERS = {
        "sort_order": "sort_order",
    }

    def _parse_bool(self, *, raw_value, default=None):
        if raw_value is None:
            return default
        if raw_value == "":
            return True

        normalized = str(raw_value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False

        return default

    def _build_queryset(self, *, request):
        queryset = (
            PublicIntegrationType.objects
            .select_related("based_to")
            .prefetch_related("translations")
            .order_by(*PublicIntegrationType._meta.ordering)
        )

        for query_param, model_field in self.BOOLEAN_FILTERS.items():
            if query_param not in request.GET:
                continue

            parsed_value = self._parse_bool(raw_value=request.GET.get(query_param), default=True)
            queryset = queryset.filter(**{model_field: parsed_value})

        for query_param, model_field in self.EXACT_FILTERS.items():
            if query_param not in request.GET:
                continue

            raw_value = request.GET.get(query_param)
            if raw_value == "":
                if query_param in {"subtype", "based_to_key"}:
                    queryset = queryset.filter(**{f"{model_field}__isnull": True})
                continue

            queryset = queryset.filter(**{model_field: raw_value})

        for query_param, model_field in self.INTEGER_FILTERS.items():
            if query_param not in request.GET:
                continue

            raw_value = request.GET.get(query_param)
            if raw_value in (None, ""):
                continue

            try:
                parsed_value = int(raw_value)
            except (TypeError, ValueError):
                continue

            queryset = queryset.filter(**{model_field: parsed_value})

        search_term = (request.GET.get("search") or "").strip()
        if search_term:
            queryset = queryset.search(search_term=search_term)

        return queryset

    def _serialize(self, *, public_integration_type, language):
        return {
            "key": public_integration_type.key,
            "type": public_integration_type.type,
            "subtype": public_integration_type.subtype,
            "based_to_key": getattr(public_integration_type.based_to, "key", None),
            "category": public_integration_type.category,
            "active": public_integration_type.active,
            "is_beta": public_integration_type.is_beta,
            "supports_open_ai_product_feed": public_integration_type.supports_open_ai_product_feed,
            "logo_png": get_public_integration_asset_url(
                integration=public_integration_type,
                field_name="logo_png",
            ),
            "logo_svg": get_public_integration_asset_url(
                integration=public_integration_type,
                field_name="logo_svg",
            ),
            "sort_order": public_integration_type.sort_order,
            "name": public_integration_type.name(language=language),
            "description": public_integration_type.description(language=language),
        }

    def get(self, request, *args, **kwargs):
        language = (request.GET.get("language") or "").strip() or None
        queryset = self._build_queryset(request=request)

        return JsonResponse(
            {
                "count": queryset.count(),
                "results": [
                    self._serialize(
                        public_integration_type=public_integration_type,
                        language=language,
                    )
                    for public_integration_type in queryset
                ],
            }
        )
