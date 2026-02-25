from __future__ import annotations

from typing import Any

from media.models import Media, MediaProductThrough
from sales_channels.factories.mixins import (
    ProductAssignmentMixin,
    RemoteInstanceCreateFactory,
    RemoteInstanceDeleteFactory,
    RemoteInstanceUpdateFactory,
)

class RemoteDocumentCreateFactory(RemoteInstanceCreateFactory):
    local_model_class = Media
    remote_document_default_status = None

    def __init__(
        self,
        *,
        sales_channel,
        media,
        remote_document=None,
        remote_document_type=None,
        api=None,
        media_through=None,
        remote_product=None,
        view=None,
        get_value_only: bool = False,
    ):
        super().__init__(sales_channel=sales_channel, local_instance=media, api=api)
        self.media = media
        self.remote_document = remote_document
        self.remote_document_type = remote_document_type
        self.media_through = media_through
        self.remote_product = remote_product
        self.view = view
        self.get_value_only = get_value_only

    def resolve_remote_document_type(self):
        if self.remote_document_type is not None:
            return self.remote_document_type
        if self.remote_document is not None and getattr(self.remote_document, "remote_document_type_id", None):
            self.remote_document_type = self.remote_document.remote_document_type
            return self.remote_document_type
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement resolve_remote_document_type when remote_document_type is missing."
        )

    def validate_document_before_sync(self):
        """Hook for integration validations before any local/remote sync."""
        return None

    def get_remote_document_defaults(self):
        defaults = {}
        if self.remote_document_default_status is not None:
            defaults["status"] = self.remote_document_default_status
        return defaults

    def ensure_remote_document_instance(self):
        if self.remote_document is not None:
            return self.remote_document

        self.remote_document, _ = self.remote_model_class.objects.get_or_create(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.media,
            remote_document_type=self.remote_document_type,
            defaults=self.get_remote_document_defaults(),
        )
        return self.remote_document

    def should_create_remote_document(self):
        return not str(getattr(self.remote_document, "remote_id", "") or "").strip()

    def sync_existing_remote_document(self):
        """Hook for integrations to refresh local metadata when remote document already exists."""
        return self.remote_document

    def create_remote_document(self):
        raise NotImplementedError

    def sync_remote_document(self):
        if self.should_create_remote_document():
            return self.create_remote_document()
        return self.sync_existing_remote_document()

    def run(self):
        self.remote_document_type = self.resolve_remote_document_type()
        if self.remote_document_type is None:
            return None
        self.validate_document_before_sync()
        self.ensure_remote_document_instance()

        if self.get_value_only:
            return self.remote_document

        self.set_api()
        return self.sync_remote_document()


class RemoteDocumentUpdateFactory(RemoteInstanceUpdateFactory):
    local_model_class = Media
    create_factory_class = None

    def __init__(
        self,
        *,
        sales_channel,
        media,
        remote_document=None,
        remote_document_type=None,
        api=None,
        media_through=None,
        remote_product=None,
        view=None,
        get_value_only: bool = False,
        **kwargs,
    ):
        super().__init__(
            sales_channel=sales_channel,
            local_instance=media,
            api=api,
            remote_instance=remote_document,
            **kwargs,
        )
        self.media = media
        self.remote_document = remote_document or self.remote_instance
        self.remote_document_type = remote_document_type or getattr(self.remote_document, "remote_document_type", None)
        self.media_through = media_through
        self.remote_product = remote_product
        self.view = view
        self.get_value_only = get_value_only

    def _build_create_factory_kwargs(self):
        return {
            "sales_channel": self.sales_channel,
            "media": self.media,
            "remote_document": self.remote_document,
            "remote_document_type": self.remote_document_type,
            "api": self.api,
            "media_through": self.media_through,
            "remote_product": self.remote_product,
            "view": self.view,
            "get_value_only": self.get_value_only,
        }

    def run_create_factory(self):
        if not self.create_factory_class:
            raise ValueError(f"{self.__class__.__name__} requires create_factory_class for delegated create flow.")

        create_factory = self.create_factory_class(**self._build_create_factory_kwargs())
        self.remote_document = create_factory.run()
        self.api = create_factory.api
        return self.remote_document

    def should_delegate_to_create(self):
        return self.create_factory_class is not None

    def update_remote_document(self):
        raise NotImplementedError

    def run(self):
        if self.should_delegate_to_create():
            return self.run_create_factory()
        if self.get_value_only:
            return self.remote_document
        self.set_api()
        return self.update_remote_document()


class RemoteDocumentDeleteFactory(RemoteInstanceDeleteFactory):
    local_model_class = Media
    has_remote_document_instance = True
    delete_document_through_factory = None
    document_remote_through_model_class = None
    remote_product_model_class = None
    delete_remote_instance = True

    def _get_target_remote_documents(self):
        if self.has_remote_document_instance:
            if self.remote_instance is not None:
                return [self.remote_instance]
            return list(
                self.remote_model_class.objects.filter(
                    local_instance=self.local_instance,
                    sales_channel=self.sales_channel,
                )
            )

        if not self.document_remote_through_model_class:
            return []

        remote_document_ids = list(
            self.document_remote_through_model_class.objects.filter(
                local_instance__media=self.local_instance,
                sales_channel=self.sales_channel,
            ).values_list("remote_document_id", flat=True)
        )
        if not remote_document_ids:
            return []

        return list(
            self.remote_model_class.objects.filter(
                id__in=remote_document_ids,
                sales_channel=self.sales_channel,
            )
        )

    def _call_delete_document_through_factory(self, *, association):
        if self.delete_document_through_factory is None:
            association.delete()
            return

        kwargs = {
            "sales_channel": self.sales_channel,
            "local_instance": association.local_instance,
            "remote_instance": association,
            "remote_product": association.remote_product,
            "api": self.api,
            "skip_checks": True,
        }
        try:
            factory = self.delete_document_through_factory(**kwargs)
        except TypeError:
            kwargs.pop("skip_checks", None)
            factory = self.delete_document_through_factory(**kwargs)
        factory.run()

    def _delete_document_through_associations(self, *, remote_document):
        if not self.document_remote_through_model_class:
            return

        associations = self.document_remote_through_model_class.objects.filter(
            sales_channel=self.sales_channel,
            remote_document=remote_document,
        ).select_related("remote_product", "local_instance")

        for association in associations:
            self._call_delete_document_through_factory(association=association)

    def delete_remote_document(self, *, remote_document):
        # Integrations can override to call external delete endpoints when available.
        return True

    def run(self):
        self.set_api()

        target_remote_documents = self._get_target_remote_documents()
        if not target_remote_documents:
            return

        for remote_document in target_remote_documents:
            self._delete_document_through_associations(remote_document=remote_document)
            self.delete_remote_document(remote_document=remote_document)
            if self.delete_remote_instance and remote_document.pk:
                remote_document.delete()


class RemoteDocumentProductThroughCreateFactory(ProductAssignmentMixin, RemoteInstanceCreateFactory):
    local_model_class = MediaProductThrough
    has_remote_document_instance = False
    remote_document_model_class = None
    remote_document_create_factory = None
    remote_document_update_factory = None

    def __init__(
        self,
        sales_channel,
        local_instance,
        remote_product,
        api=None,
        skip_checks=False,
    ):
        super().__init__(sales_channel=sales_channel, local_instance=local_instance, api=api)
        self.remote_product = remote_product or self.get_remote_product(local_instance.product)

        if skip_checks and self.remote_product is None:
            raise ValueError("Factory has skip checks enabled without providing the remote product.")

        self.skip_checks = skip_checks
        self.remote_document_instance = None
        self._existing_remote_assignment = None
        self._current_remote_assignment = None

        remote_model_class = getattr(self, "remote_model_class", None)
        if remote_model_class and self.remote_product and self.local_instance:
            self._current_remote_assignment = remote_model_class.objects.filter(
                local_instance=self.local_instance,
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
            ).first()

            if not self._current_remote_assignment and self.local_instance.sales_channel_id:
                self._existing_remote_assignment = self._get_existing_default_remote_assignment()

    def preflight_check(self):
        if self.skip_checks:
            return True

        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False

        return True

    def _create_remote_document(self, *, remote_document_instance=None):
        if not self.remote_document_create_factory:
            raise ValueError(
                f"{self.__class__.__name__} requires remote_document_create_factory when has_remote_document_instance=True."
            )

        factory = self.remote_document_create_factory(
            sales_channel=self.sales_channel,
            media=self.local_instance.media,
            remote_document=remote_document_instance,
            api=self.api,
            media_through=self.local_instance,
            remote_product=self.remote_product,
        )
        remote_document = factory.run()
        self.api = factory.api
        return remote_document

    def _update_remote_document(self, *, remote_document_instance):
        if not self.remote_document_update_factory:
            return remote_document_instance

        factory = self.remote_document_update_factory(
            sales_channel=self.sales_channel,
            media=self.local_instance.media,
            remote_document=remote_document_instance,
            api=self.api,
            media_through=self.local_instance,
            remote_product=self.remote_product,
        )
        remote_document = factory.run()
        self.api = factory.api
        return remote_document

    def create_or_update_remote_document(self):
        if not self.has_remote_document_instance:
            return

        if self.remote_document_model_class is None:
            raise ValueError(
                f"{self.__class__.__name__} requires remote_document_model_class when has_remote_document_instance=True."
            )

        remote_document = self.remote_document_model_class.objects.filter(
            local_instance=self.local_instance.media,
            sales_channel=self.sales_channel,
        ).first()
        if remote_document is None:
            remote_document = self._create_remote_document()
        else:
            remote_document = self._update_remote_document(remote_document_instance=remote_document)

        self.remote_document_instance = remote_document

    def preflight_process(self):
        self.create_or_update_remote_document()

    def customize_remote_instance_data(self):
        self.remote_instance_data["remote_product"] = self.remote_product
        if self.has_remote_document_instance:
            self.remote_instance_data["remote_document"] = self.remote_document_instance
        return self.remote_instance_data

    def _get_existing_default_remote_assignment(self):
        default_assignment = MediaProductThrough.objects.filter(
            product=self.local_instance.product,
            media=self.local_instance.media,
            sales_channel__isnull=True,
        ).first()
        if not default_assignment:
            return None

        remote_model_class = getattr(self, "remote_model_class", None)
        if remote_model_class is None:
            return None

        return remote_model_class.objects.filter(
            local_instance=default_assignment,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        ).select_related("remote_document").first()

    def _reuse_existing_remote_assignment(self):
        existing_remote_assignment = self._existing_remote_assignment
        if existing_remote_assignment is None:
            return

        if (
            self.has_remote_document_instance
            and self.remote_document_instance is None
            and hasattr(existing_remote_assignment, "remote_document")
        ):
            self.remote_document_instance = existing_remote_assignment.remote_document

        self.build_remote_instance_data()
        self.customize_remote_instance_data()
        self.initialize_remote_instance()

        update_fields = set(self.remote_instance_data.keys())
        for attr in ("remote_id", "remote_document", "successfully_created", "outdated", "outdated_since"):
            if hasattr(existing_remote_assignment, attr):
                setattr(self.remote_instance, attr, getattr(existing_remote_assignment, attr))
                update_fields.add(attr)

        self.remote_instance.save(update_fields=list(update_fields))

    def run(self):
        if self._current_remote_assignment:
            if not self.preflight_check():
                return
            self.remote_instance = self._current_remote_assignment
            return

        if not self.preflight_check():
            return

        self.set_api()
        self.preflight_process()
        if self.has_remote_document_instance and self.remote_document_instance is None:
            self.remote_instance = None
            return

        if self._existing_remote_assignment:
            self._reuse_existing_remote_assignment()
            return

        self.build_payload()
        self.customize_payload()
        self.build_remote_instance_data()
        self.customize_remote_instance_data()
        self.initialize_remote_instance()
        self.create()


class RemoteDocumentProductThroughUpdateFactory(ProductAssignmentMixin, RemoteInstanceUpdateFactory):
    local_model_class = MediaProductThrough
    has_remote_document_instance = False
    remote_document_model_class = None
    remote_document_create_factory = None
    remote_document_update_factory = None
    create_factory_class = None

    def __init__(
        self,
        sales_channel,
        local_instance,
        remote_product,
        api=None,
        skip_checks=False,
        remote_instance=None,
    ):
        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            api=api,
            remote_instance=remote_instance,
            remote_product=remote_product,
        )
        if skip_checks and self.remote_product is None:
            raise ValueError("Factory has skip checks enabled without providing the remote product.")
        self.skip_checks = skip_checks
        self.remote_document_instance = None

    def preflight_check(self):
        if self.skip_checks:
            return True
        if not self.remote_product:
            return False
        if not self.assigned_to_website():
            return False
        return True

    def preflight_process(self):
        if not self.has_remote_document_instance:
            return

        if self.remote_document_model_class is None:
            raise ValueError(
                f"{self.__class__.__name__} requires remote_document_model_class when has_remote_document_instance=True."
            )

        remote_document = self.remote_document_model_class.objects.filter(
            local_instance=self.local_instance.media,
            sales_channel=self.sales_channel,
        ).first()

        if remote_document is None:
            if not self.remote_document_create_factory:
                raise ValueError(
                    f"{self.__class__.__name__} requires remote_document_create_factory when has_remote_document_instance=True."
                )

            create_factory = self.remote_document_create_factory(
                sales_channel=self.sales_channel,
                media=self.local_instance.media,
                api=self.api,
                media_through=self.local_instance,
                remote_product=self.remote_product,
            )
            remote_document = create_factory.run()
            self.api = create_factory.api
        elif self.remote_document_update_factory:
            update_factory = self.remote_document_update_factory(
                sales_channel=self.sales_channel,
                media=self.local_instance.media,
                remote_document=remote_document,
                api=self.api,
                media_through=self.local_instance,
                remote_product=self.remote_product,
            )
            remote_document = update_factory.run()
            self.api = update_factory.api

        self.remote_document_instance = remote_document

        if (
            self.remote_instance
            and self.remote_document_instance is not None
            and self.remote_instance.remote_document_id != self.remote_document_instance.id
        ):
            self.remote_instance.remote_document = self.remote_document_instance
            self.remote_instance.save(update_fields=["remote_document"])

    def run(self):
        if not self.preflight_check():
            return

        self.set_api()
        self.preflight_process()
        if self.has_remote_document_instance and self.remote_document_instance is None:
            self.remote_instance = None
            return

        if self.remote_instance is None and self.create_factory_class:
            factory_kwargs = {
                "sales_channel": self.sales_channel,
                "local_instance": self.local_instance,
                "remote_product": self.remote_product,
                "api": self.api,
                "skip_checks": True,
                "get_value_only": getattr(self, "get_value_only", False),
            }
            if hasattr(self, "view"):
                factory_kwargs["view"] = self.view

            try:
                create_factory = self.create_factory_class(**factory_kwargs)
            except TypeError:
                factory_kwargs.pop("get_value_only", None)
                factory_kwargs.pop("view", None)
                create_factory = self.create_factory_class(**factory_kwargs)
            create_factory.run()
            self.remote_instance = create_factory.remote_instance
            return

        if self.remote_instance is None:
            return

        self.build_payload()
        self.customize_payload()
        if self.needs_update() and self.additional_update_check():
            self.update()


class RemoteDocumentProductThroughDeleteFactory(ProductAssignmentMixin, RemoteInstanceDeleteFactory):
    local_model_class = MediaProductThrough

    def __init__(
        self,
        sales_channel,
        remote_product,
        local_instance=None,
        api=None,
        skip_checks=False,
        remote_instance=None,
    ):
        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            api=api,
            remote_instance=remote_instance,
            remote_product=remote_product,
        )
        if skip_checks and self.remote_product is None:
            raise ValueError("Factory has skip checks enabled without providing the remote product.")
        self.skip_checks = skip_checks

    def preflight_check(self):
        if self.skip_checks:
            return True
        if not self.remote_product:
            return False
        if not self.assigned_to_website():
            return False
        return True
