from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from django.db import transaction
import logging

from integrations.helpers import get_import_path
from integrations.tasks import add_task_to_queue

logger = logging.getLogger(__name__)


@dataclass
class GuardResult:
    allowed: bool
    reason: str | None = None
    changed_fields: list[str] = field(default_factory=list)
    sync_type: str | None = None


@dataclass
class TaskTarget:
    sales_channel: Any
    remote_product: Any | None = None
    remote_instance: Any | None = None
    sales_channel_view: Any | None = None
    view_assign: Any | None = None


class AddTaskConfigError(Exception):
    pass


class AddTaskBase:
    live = True
    sales_channel_class = None
    sync_type = None
    reason = None
    product_task_fallback = None
    require_sales_channel_class = False
    require_remote_class = False
    require_view_assign_model = False

    def __init__(
        self,
        *,
        task_func,
        multi_tenant_company,
        number_of_remote_requests=None,
        sales_channels_filter_kwargs=None,
    ):
        self.task_func = task_func
        self.multi_tenant_company = multi_tenant_company
        self.number_of_remote_requests = number_of_remote_requests
        self.sales_channels_filter_kwargs = sales_channels_filter_kwargs or {}
        self.extra_task_kwargs: dict[str, Any] = {}
        self.validate_config()

    def validate_config(self):
        if self.__class__ is AddTaskBase:
            raise AddTaskConfigError("AddTaskBase must be subclassed before use.")

        if self.task_func is None:
            raise AddTaskConfigError("task_func must be provided.")

        if self.multi_tenant_company is None:
            raise AddTaskConfigError("multi_tenant_company must be provided.")

        if self.require_sales_channel_class and self.sales_channel_class is None:
            raise AddTaskConfigError("sales_channel_class must be configured for this task runner.")

        if not self.live and self.sync_type is None:
            raise AddTaskConfigError("sync_type must be set when live sync is disabled.")

        if self.require_remote_class and getattr(self, "remote_class", None) is None:
            raise AddTaskConfigError("remote_class must be configured for this task runner.")

        if self.require_view_assign_model and getattr(self, "view_assign_model", None) is None:
            raise AddTaskConfigError("view_assign_model must be configured for this task runner.")

        self.validate_config_extra()

    def validate_config_extra(self):
        pass

    def set_extra_task_kwargs(self, **kwargs):
        self.extra_task_kwargs.update(kwargs)

    def get_sales_channels_filter_kwargs(self):
        filter_kwargs = dict(self.sales_channels_filter_kwargs or {})
        filter_kwargs["multi_tenant_company"] = self.multi_tenant_company
        return filter_kwargs

    def get_sales_channels(self) -> Iterable[Any]:
        if self.sales_channel_class is None:
            return []
        return self.sales_channel_class.objects.filter(**self.get_sales_channels_filter_kwargs())

    def get_targets(self, *, sales_channel) -> Iterable[TaskTarget]:
        yield TaskTarget(sales_channel=sales_channel)

    def guard(self, *, target: TaskTarget) -> GuardResult:
        resolved_channel = getattr(target.sales_channel, "get_real_instance", None)
        if resolved_channel:
            sales_channel = resolved_channel()
        else:
            sales_channel = target.sales_channel

        if self.sales_channel_class and not isinstance(sales_channel, self.sales_channel_class):
            return GuardResult(allowed=False, reason="sales_channel_type_mismatch")
        if hasattr(sales_channel, "active") and not sales_channel.active:
            return GuardResult(allowed=False, reason="sales_channel_inactive")

        return GuardResult(allowed=True)

    def build_task_kwargs(self, *, target: TaskTarget) -> dict[str, Any]:
        return {
            "sales_channel_id": target.sales_channel.id,
            **self.extra_task_kwargs,
        }

    def build_product_task_kwargs(self, *, target: TaskTarget) -> dict[str, Any]:
        task_kwargs = {
            "sales_channel_id": target.sales_channel.id,
        }
        view_id = getattr(target.sales_channel_view, "id", target.sales_channel_view)
        if view_id:
            task_kwargs["view_id"] = view_id
        if target.remote_product:
            task_kwargs["remote_product_id"] = target.remote_product.id
            local_instance_id = getattr(target.remote_product, "local_instance_id", None)
            if local_instance_id:
                task_kwargs["product_id"] = local_instance_id
        return task_kwargs

    def _create_sync_request_record(
        self,
        *,
        remote_product,
        sales_channel,
        sales_channel_view_id,
        sync_type,
        reason,
        task_func_path,
        task_kwargs,
        status,
        skipped_for=None,
    ):
        from sales_channels.models import SyncRequest

        return SyncRequest.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_product=remote_product,
            sales_channel=sales_channel,
            sales_channel_view_id=sales_channel_view_id,
            sync_type=sync_type,
            reason=reason,
            task_func_path=task_func_path,
            task_kwargs=task_kwargs,
            number_of_remote_requests=self.number_of_remote_requests,
            status=status,
            skipped_for=skipped_for,
        )

    def get_integration_id(self, *, target: TaskTarget) -> int:
        return target.sales_channel.id

    def send_to_queue(self, *, target: TaskTarget, guard_result: GuardResult):
        task_kwargs = self.build_task_kwargs(target=target)
        integration_id = self.get_integration_id(target=target)

        transaction.on_commit(
            lambda lb_task_kwargs=task_kwargs, integration_id=integration_id: add_task_to_queue(
                integration_id=integration_id,
                task_func_path=get_import_path(self.task_func),
                task_kwargs=lb_task_kwargs,
                number_of_remote_requests=self.number_of_remote_requests,
            )
        )

    def _get_pending_requests_for_remote(
        self,
        *,
        remote_product,
        sales_channel,
        sales_channel_view_id,
    ):
        from sales_channels.models import SyncRequest

        return SyncRequest.objects.filter(
            status=SyncRequest.STATUS_PENDING,
            sales_channel=sales_channel,
            sales_channel_view_id=sales_channel_view_id,
            remote_product=remote_product,
        )

    def _get_pending_product_request(
        self,
        *,
        remote_product,
        sales_channel,
        sales_channel_view_id,
    ):
        from sales_channels.models import SyncRequest

        return (
            self._get_pending_requests_for_remote(
                remote_product=remote_product,
                sales_channel=sales_channel,
                sales_channel_view_id=sales_channel_view_id,
            )
            .filter(sync_type=SyncRequest.TYPE_PRODUCT)
            .first()
        )

    def _get_remote_product_siblings(self, *, remote_product):
        from sales_channels.models import RemoteProduct

        parent = getattr(remote_product, "remote_parent_product", None)
        if not parent:
            return RemoteProduct.objects.none()

        return RemoteProduct.objects.filter(
            remote_parent_product=parent,
            sales_channel=remote_product.sales_channel,
        )

    def _get_pending_product_requests_for_siblings(
        self,
        *,
        siblings,
        sales_channel,
        sales_channel_view_id,
    ):
        from sales_channels.models import SyncRequest

        sibling_ids = siblings.values_list("id", flat=True)
        return SyncRequest.objects.filter(
            status=SyncRequest.STATUS_PENDING,
            sales_channel=sales_channel,
            sales_channel_view_id=sales_channel_view_id,
            sync_type=SyncRequest.TYPE_PRODUCT,
            remote_product_id__in=sibling_ids,
        )

    def _create_product_request(
        self,
        *,
        remote_product,
        sales_channel,
        sales_channel_view_id,
        reason,
    ):
        from sales_channels.models import SyncRequest

        if self.product_task_fallback is None:
            raise AddTaskConfigError("product_task_fallback must be configured to upgrade to product sync.")

        product_target = TaskTarget(
            sales_channel=sales_channel,
            remote_product=remote_product,
            sales_channel_view=sales_channel_view_id,
        )
        return self._create_sync_request_record(
            remote_product=remote_product,
            sales_channel=sales_channel,
            sales_channel_view_id=sales_channel_view_id,
            sync_type=SyncRequest.TYPE_PRODUCT,
            reason=reason,
            task_func_path=get_import_path(self.product_task_fallback),
            task_kwargs=self.build_product_task_kwargs(target=product_target),
            status=SyncRequest.STATUS_PENDING,
        )

    def _mark_requests_skipped(self, *, queryset, skipped_for):
        from sales_channels.models import SyncRequest

        if not queryset.exists():
            return

        queryset.update(
            status=SyncRequest.STATUS_SKIPPED,
            skipped_for=skipped_for,
        )

    def _create_skipped_request(
        self,
        *,
        remote_product,
        sales_channel,
        sales_channel_view_id,
        sync_type,
        reason,
        task_func_path,
        task_kwargs,
        skipped_for,
    ):
        from sales_channels.models import SyncRequest

        self._create_sync_request_record(
            remote_product=remote_product,
            sales_channel=sales_channel,
            sales_channel_view_id=sales_channel_view_id,
            sync_type=sync_type,
            reason=reason,
            task_func_path=task_func_path,
            task_kwargs=task_kwargs,
            status=SyncRequest.STATUS_SKIPPED,
            skipped_for=skipped_for,
        )

    def _escalate_product_to_parent_if_needed(
        self,
        *,
        product_request,
        base_remote_product,
        sales_channel,
        sales_channel_view_id,
        reason,
    ):
        from sales_channels.models import SyncRequest

        if not getattr(base_remote_product, "is_variation", False):
            return product_request

        parent = getattr(base_remote_product, "remote_parent_product", None)
        if parent is None:
            return product_request

        siblings = self._get_remote_product_siblings(remote_product=base_remote_product)
        if not siblings.exclude(id=base_remote_product.id).exists():
            # Example: variation has no siblings, so no parent escalation is needed.
            return product_request

        sibling_pending = self._get_pending_product_requests_for_siblings(
            siblings=siblings,
            sales_channel=sales_channel,
            sales_channel_view_id=sales_channel_view_id,
        )

        # Example: a parent product request already exists, so all sibling product requests
        # should be skipped to that parent request.
        parent_request = self._get_pending_product_request(
            remote_product=parent,
            sales_channel=sales_channel,
            sales_channel_view_id=sales_channel_view_id,
        )
        if not parent_request:
            # Example: no parent product request exists, create one and skip sibling product requests to it.
            parent_request = self._create_product_request(
                remote_product=parent,
                sales_channel=sales_channel,
                sales_channel_view_id=sales_channel_view_id,
                reason=reason,
            )

        self._mark_requests_skipped(queryset=sibling_pending, skipped_for=parent_request)
        return parent_request

    def create_sync_request(self, *, target: TaskTarget, guard_result: GuardResult):
        from sales_channels.models import SyncRequest

        if target.remote_product is None:
            return

        sync_type = guard_result.sync_type or self.sync_type
        if not sync_type:
            return

        sales_channel_view = target.sales_channel_view
        sales_channel_view_id = getattr(sales_channel_view, "id", sales_channel_view)
        base_remote_product = target.remote_product
        sales_channel = target.sales_channel
        sync_request_reason = guard_result.reason or self.reason
        task_func_path = get_import_path(self.task_func)
        task_kwargs = self.build_task_kwargs(target=target)

        # Step 1: Same-remote-product dedupe → upgrade to product (no updates, only new rows).
        # 1. Look at pending sync requests for the same remote_product + view.
        # 2. If there are any non-product pending:
        #    - If there is already a pending product request:
        #      - Create the new request as skipped, pointing skipped_for to the existing product request.
        #      - Mark the existing non-product pending requests as skipped (also pointing to that product request).
        #      - Stop (no further escalation needed at this level).
        #    - If there is no pending product:
        #      - Create a new product pending request (product fallback task/kwargs).
        #      - Mark all existing non-product pending as skipped, pointing skipped_for to the new product request.
        #      - The current incoming request is represented by that product request, but we still
        #        create the current one as skipped for transparency.
        # 3. If there are no non-product pending:
        #    - Create the request as-is (non-product), and proceed to step 2 only if it’s product.
        pending_same = self._get_pending_requests_for_remote(
            remote_product=base_remote_product,
            sales_channel=sales_channel,
            sales_channel_view_id=sales_channel_view_id,
        )
        pending_non_product = pending_same.exclude(sync_type=SyncRequest.TYPE_PRODUCT)
        existing_product = pending_same.filter(sync_type=SyncRequest.TYPE_PRODUCT).first()

        product_request = None

        if pending_non_product.exists():
            # Example: existing pending "property"/"content" for this remote product.
            # Upgrade to a single pending "product" request, and mark the others (including current)
            # as skipped_for that product request.
            if not existing_product:
                existing_product = self._create_product_request(
                    remote_product=base_remote_product,
                    sales_channel=sales_channel,
                    sales_channel_view_id=sales_channel_view_id,
                    reason=sync_request_reason,
                )
            product_request = existing_product
            self._create_skipped_request(
                remote_product=base_remote_product,
                sales_channel=sales_channel,
                sales_channel_view_id=sales_channel_view_id,
                sync_type=sync_type,
                reason=sync_request_reason,
                task_func_path=task_func_path,
                task_kwargs=task_kwargs,
                skipped_for=product_request,
            )
            self._mark_requests_skipped(queryset=pending_non_product, skipped_for=product_request)
        else:
            if sync_type == SyncRequest.TYPE_PRODUCT:
                # Example: incoming is already "product" and there are no other non-product pending.
                # Reuse the existing product request or create a new pending one.
                if not existing_product:
                    existing_product = self._create_product_request(
                        remote_product=base_remote_product,
                        sales_channel=sales_channel,
                        sales_channel_view_id=sales_channel_view_id,
                        reason=sync_request_reason,
                    )
                product_request = existing_product
            else:
                # Example: incoming is "price" and there are no other pending requests.
                # Create a pending non-product request and stop (no sibling escalation).
                self._create_sync_request_record(
                    remote_product=base_remote_product,
                    sales_channel=sales_channel,
                    sales_channel_view_id=sales_channel_view_id,
                    sync_type=sync_type,
                    reason=sync_request_reason,
                    task_func_path=task_func_path,
                    task_kwargs=task_kwargs,
                    status=SyncRequest.STATUS_PENDING,
                )
                return

        if product_request is None:
            return

        # Sibling escalation (only for product requests).
        self._escalate_product_to_parent_if_needed(
            product_request=product_request,
            base_remote_product=base_remote_product,
            sales_channel=sales_channel,
            sales_channel_view_id=sales_channel_view_id,
            reason=sync_request_reason,
        )

    def log_guard_blocked(self, *, target: TaskTarget, guard_result: GuardResult):
        logger.debug(
            "Guard blocked task: reason=%s sync_type=%s sales_channel_id=%s remote_product_id=%s "
            "remote_instance_id=%s sales_channel_view_id=%s",
            guard_result.reason,
            guard_result.sync_type or self.sync_type,
            getattr(target.sales_channel, "id", None),
            getattr(target.remote_product, "id", None),
            getattr(target.remote_instance, "id", None),
            getattr(target.sales_channel_view, "id", target.sales_channel_view),
        )

    def run(self):
        for sales_channel in self.get_sales_channels():
            for target in self.get_targets(sales_channel=sales_channel):
                guard_result = self.guard(target=target)
                if not guard_result.allowed:
                    self.log_guard_blocked(target=target, guard_result=guard_result)
                    continue

                if self.live:
                    self.send_to_queue(target=target, guard_result=guard_result)
                else:
                    self.create_sync_request(target=target, guard_result=guard_result)


class ChannelScopedAddTask(AddTaskBase):
    require_sales_channel_class = True

    def __init__(self, *, multi_tenant_company, **kwargs):
        kwargs.setdefault("multi_tenant_company", multi_tenant_company)
        super().__init__(**kwargs)

    def get_sales_channels_filter_kwargs(self):
        filter_kwargs = super().get_sales_channels_filter_kwargs()
        if "active" not in filter_kwargs:
            filter_kwargs["active"] = True
        filter_kwargs["multi_tenant_company"] = self.multi_tenant_company
        return filter_kwargs


class RuleScopedAddTask(ChannelScopedAddTask):
    def __init__(self, *, rule, **kwargs):
        self.rule = rule
        kwargs.setdefault("multi_tenant_company", rule.multi_tenant_company)
        super().__init__(**kwargs)

    def get_sales_channels(self) -> Iterable[Any]:
        from properties.models import ProductPropertiesRule

        filter_kwargs = self.get_sales_channels_filter_kwargs()
        specialized_channel_ids = set()

        if self.rule.sales_channel_id:
            filter_kwargs["id"] = self.rule.sales_channel_id
        else:
            specialized_channel_ids = set(
                ProductPropertiesRule.objects.filter(
                    multi_tenant_company=self.rule.multi_tenant_company,
                    product_type=self.rule.product_type,
                    sales_channel__isnull=False,
                ).values_list("sales_channel_id", flat=True)
            )

        for sales_channel in self.sales_channel_class.objects.filter(**filter_kwargs):
            if not self.rule.sales_channel_id and sales_channel.id in specialized_channel_ids:
                continue
            yield sales_channel


class ProductScopedAddTask(ChannelScopedAddTask):
    def __init__(self, *, product, **kwargs):
        self.product = product
        kwargs.setdefault("multi_tenant_company", product.multi_tenant_company)
        super().__init__(**kwargs)

    def build_task_kwargs(self, *, target: TaskTarget) -> dict[str, Any]:
        task_kwargs = super().build_task_kwargs(target=target)
        if target.remote_product:
            task_kwargs["remote_product_id"] = target.remote_product.id
        return task_kwargs

    def guard(self, *, target: TaskTarget) -> GuardResult:
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result
        remote_product = target.remote_product
        if remote_product is not None and not remote_product.successfully_created:
            return GuardResult(
                allowed=False,
                reason="remote_product_not_successfully_created",
            )
        return guard_result

    def get_targets(self, *, sales_channel) -> Iterable[TaskTarget]:
        from sales_channels.models import RemoteProduct

        for remote_product in RemoteProduct.objects.filter(
            local_instance=self.product,
            sales_channel=sales_channel,
        ).iterator():
            yield TaskTarget(
                sales_channel=sales_channel,
                remote_product=remote_product,
            )


class ProductPropertyAddTask(ProductScopedAddTask):
    sync_type = "property"

    def guard(self, *, target: TaskTarget) -> GuardResult:
        # Guard intent (property):
        # - extra check for internal information to skip
        # - Only meaningful for products where the property is actually used on the channel.
        # - For marketplaces: must pass integration-specific mapping checks
        #   (property mapped, used in category, select/multi-select value mapped).
        # - For variations: if the property change should escalate to parent, do it in create_sync_request.
        # - Skip when no effective change would happen (e.g., property not relevant to the channel/rule).
        # TODO: add property-specific guards.
        return GuardResult(allowed=True)


class ProductPriceAddTask(ProductScopedAddTask):
    sync_type = "price"

    def guard(self, *, target: TaskTarget) -> GuardResult:
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result
        # Guard intent (price):
        # - Compute effective channel price (currency, discount, rounding).
        # - Compare against last known remote price payload/hash; if unchanged, skip.
        # - For configurable products, pricing changes usually belong to variations only.
        # TODO: add price-specific guards.
        return guard_result


class ProductContentAddTask(ProductScopedAddTask):
    sync_type = "content"

    def guard(self, *, target: TaskTarget) -> GuardResult:
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result
        # Guard intent (content):
        # - Resolve effective content for the channel view (language + overrides).
        # - If default content is overridden by channel-specific content, ignore default changes.
        # - Compare against last known remote content payload/hash; if unchanged, skip.
        # TODO: add content-specific guards.
        return guard_result


class ProductEanCodeAddTask(ProductScopedAddTask):
    sync_type = "product"

    def guard(self, *, target: TaskTarget) -> GuardResult:
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result
        # Guard intent (EAN):
        # - Only allow when the channel supports EAN updates.
        # - Skip if the effective value matches the remote value.
        # TODO: add EAN-code-specific guards.
        return guard_result


class ProductImagesAddTask(ProductScopedAddTask):
    sync_type = "images"

    def guard(self, *, target: TaskTarget) -> GuardResult:
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result
        # Guard intent (images):
        # - Respect channel-specific overrides; default image changes should not affect
        #   channels with their own image sets.
        # - Compare effective image set/hash before/after; if unchanged, skip.
        # TODO: add image-specific guards.
        return guard_result


class ProductUpdateAddTask(ProductScopedAddTask):
    sync_type = "product"

    def guard(self, *, target: TaskTarget) -> GuardResult:
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result
        # Guard intent (product update):
        # - Use for identity/availability changes (active, SKU, identifiers).
        # - Skip if changes do not impact the channel’s effective payload.
        # TODO: add product-update guards.
        return guard_result


class ProductFullSyncAddTask(ProductScopedAddTask):
    sync_type = "product"

    def guard(self, *, target: TaskTarget) -> GuardResult:
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result
        # Guard intent (full sync):
        # - Use as fallback when multiple changes require a full resync.
        # - Skip when remote product is not ready or no effective changes are present.
        # TODO: add full-sync guards.
        return guard_result


class DeleteScopedAddTask(ChannelScopedAddTask):
    require_remote_class = True

    def build_task_kwargs(self, *, target: TaskTarget) -> dict[str, Any]:
        task_kwargs = super().build_task_kwargs(target=target)
        if target.remote_instance:
            task_kwargs["remote_instance"] = target.remote_instance.id
        return task_kwargs

    def __init__(
        self,
        *,
        local_instance_id,
        is_variation=False,
        is_multiple=False,
        **kwargs,
    ):
        self.local_instance_id = local_instance_id
        self.is_variation = is_variation
        self.is_multiple = is_multiple
        super().__init__(**kwargs)

    def get_targets(self, *, sales_channel) -> Iterable[TaskTarget]:
        get_kwargs = {
            "local_instance_id": self.local_instance_id,
            "sales_channel": sales_channel,
        }
        if self.is_variation:
            get_kwargs["is_variation"] = False

        if self.is_multiple:
            for remote_instance in self.remote_class.objects.filter(**get_kwargs):
                yield TaskTarget(
                    sales_channel=sales_channel,
                    remote_instance=remote_instance,
                )
        else:
            remote_instance = self.remote_class.objects.filter(**get_kwargs).first()
            if remote_instance:
                yield TaskTarget(
                    sales_channel=sales_channel,
                    remote_instance=remote_instance,
                )


class ProductDeleteScopedAddTask(ProductScopedAddTask):
    require_remote_class = True

    def __init__(self, *, local_instance_id, **kwargs):
        self.local_instance_id = local_instance_id
        super().__init__(**kwargs)

    def build_task_kwargs(self, *, target: TaskTarget) -> dict[str, Any]:
        task_kwargs = super().build_task_kwargs(target=target)
        if target.remote_product:
            task_kwargs["remote_product_id"] = target.remote_product.id
        if target.remote_instance:
            task_kwargs["remote_instance_id"] = target.remote_instance.id
        return task_kwargs

    def get_targets(self, *, sales_channel) -> Iterable[TaskTarget]:
        from sales_channels.models import RemoteProduct

        for remote_product in RemoteProduct.objects.filter(
            local_instance=self.product,
            sales_channel=sales_channel,
        ).iterator():
            remote_instance = self.remote_class.objects.filter(
                local_instance_id=self.local_instance_id,
                sales_channel=sales_channel,
                remote_product_id=remote_product.id,
            ).first()
            if remote_instance:
                yield TaskTarget(
                    sales_channel=sales_channel,
                    remote_product=remote_product,
                    remote_instance=remote_instance,
                )


class ViewScopedAddTask(ProductScopedAddTask):
    view_assign_model = None
    require_view_assign_model = True

    def get_targets(self, *, sales_channel) -> Iterable[TaskTarget]:
        from sales_channels.models import RemoteProduct

        remote_products = {
            remote_product.id: remote_product
            for remote_product in RemoteProduct.objects.filter(
                local_instance=self.product,
                sales_channel=sales_channel,
            )
        }

        if not remote_products:
            return

        assign_rows = (
            self.view_assign_model.objects.filter(
                product=self.product,
                sales_channel_view__sales_channel_id=sales_channel.id,
            )
            .values_list("sales_channel_view_id", "remote_product_id")
            .distinct()
        )

        for view_id, assign_remote_product_id in assign_rows:
            if assign_remote_product_id and assign_remote_product_id in remote_products:
                effective_products = [remote_products[assign_remote_product_id]]
            else:
                effective_products = list(remote_products.values())

            for remote_product in effective_products:
                yield TaskTarget(
                    sales_channel=sales_channel,
                    remote_product=remote_product,
                    sales_channel_view=view_id,
                )


class SingleViewAddTask(AddTaskBase):
    def __init__(self, *, view, **kwargs):
        self.view = view
        self.sales_channel = view.sales_channel
        kwargs.setdefault("multi_tenant_company", self.sales_channel.multi_tenant_company)
        super().__init__(**kwargs)

    def get_sales_channels(self) -> Iterable[Any]:
        return [self.sales_channel]

    def get_targets(self, *, sales_channel) -> Iterable[TaskTarget]:
        yield TaskTarget(
            sales_channel=sales_channel,
            sales_channel_view=self.view,
        )

    def build_task_kwargs(self, *, target: TaskTarget) -> dict[str, Any]:
        view_id = target.sales_channel_view.id
        return {
            "sales_channel_id": target.sales_channel.id,
            "view_id": view_id,
            **self.extra_task_kwargs,
        }


class SingleChannelAddTask(AddTaskBase):
    def __init__(self, *, sales_channel, **kwargs):
        self.sales_channel = sales_channel
        kwargs.setdefault("multi_tenant_company", self.sales_channel.multi_tenant_company)
        super().__init__(**kwargs)

    def get_sales_channels(self) -> Iterable[Any]:
        return [self.sales_channel]

    def get_targets(self, *, sales_channel) -> Iterable[TaskTarget]:
        yield TaskTarget(sales_channel=sales_channel)
