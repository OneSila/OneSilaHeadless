from imports_exports.decorators import handle_import_exception
from imports_exports.factories.products import ImportProductInstance
from imports_exports.factories.properties import ImportProductPropertiesRuleInstance, ImportPropertySelectValueInstance, \
    ImportPropertyInstance
from imports_exports.models import Import, ImportReport
from notifications.factories.email import SendImportReportEmailFactory
import traceback
import math
from core.decorators import timeit_and_log
from core.helpers import safe_run_task

from core.helpers import ensure_serializable

import logging
logger = logging.getLogger(__name__)


class ImportMixin:
    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = False

    def __init__(self, import_process, language=None):
        self.import_process = import_process
        self.language = language

        self.total_import_instances_cnt = 0
        self.total_imported_instances = 0
        self.current_percent = 0
        self._threshold_chunk = 1
        self._broken_records =[]

    def calculate_percentage(self):
        self.total_import_instances_cnt = self.get_total_instances()
        self.total_imported_instances = 0
        self.current_percent = 0
        self.set_threshold_chunk()

    def set_threshold_chunk(self):
        self._threshold_chunk = max(1, math.floor(self.total_import_instances_cnt * 0.01))

    def update_percentage(self, to_add=1):
        self.total_imported_instances += to_add

        if self.total_imported_instances % self._threshold_chunk == 0:
            new_percent = math.floor((self.total_imported_instances / self.total_import_instances_cnt) * 100)

            if new_percent > self.current_percent:
                self.current_percent = new_percent
                self.import_process.percentage = self.current_percent
                self.import_process.save()

    def strat_process(self):
        self.import_process.status = Import.STATUS_PROCESSING
        self.import_process.percentage = 0
        self.import_process.save()

    def mark_success(self):
        self.import_process.status = Import.STATUS_SUCCESS
        self.import_process.percentage = 100
        self.import_process.save()

        from imports_exports.signals import import_success
        import_success.send(sender=self.import_process.__class__, instance=self.import_process)

        self.on_success()

    def mark_failure(self):
        self.import_process.status = Import.STATUS_FAILED
        self.import_process.percentage = 100
        self.import_process.error_traceback = traceback.format_exc()
        self.import_process.save()

        self.on_fail()

    def on_success(self):
        pass

    def on_fail(self):
        pass

    def get_total_instances(self):
        raise NotImplementedError("'get_total_instances' needs to be implemented in the subclass!")

    # --------------------
    # PRODUCTS
    # --------------------
    def get_products_data(self):
        raise NotImplementedError("'get_products_data' needs to be implemented in the subclass!")

    def get_structured_product_data(self, product_data):
        raise NotImplementedError("'get_structured_product_data' needs to be implemented in the subclass!")

    def get_final_product_data_from_log(self, log_instance):
        return log_instance

    def update_product_log_instance(self, log_instance, import_instance):
        pass

    # --------------------
    # PROPERTIES
    # --------------------
    def get_properties_data(self):
        raise NotImplementedError("'get_properties_data' needs to be implemented in the subclass!")

    def get_structured_property_data(self, property_data):
        raise NotImplementedError("'get_structured_property_data' needs to be implemented in the subclass!")

    def get_final_property_data_from_log(self, log_instance):
        return log_instance

    def update_property_log_instance(self, log_instance, import_instance):
        pass

    # --------------------
    # SELECT VALUES
    # --------------------
    def get_select_values_data(self):
        raise NotImplementedError("'get_select_values_data' needs to be implemented in the subclass!")

    def get_structured_select_value_data(self, value_data):
        raise NotImplementedError("'get_structured_select_value_data' needs to be implemented in the subclass!")

    def get_final_select_value_data_from_log(self, log_instance):
        return log_instance

    def update_select_value_log_instance(self, log_instance, import_instance):
        pass

    # --------------------
    # RULES
    # --------------------
    def get_rules_data(self):
        raise NotImplementedError("'get_rules_data' needs to be implemented in the subclass!")

    def get_structured_rule_data(self, rule_data):
        raise NotImplementedError("'get_structured_rule_data' needs to be implemented in the subclass!")

    def get_final_rule_data_from_log(self, log_instance):
        return log_instance

    def update_rule_log_instance(self, log_instance, import_instance, rule_data):
        pass

    def update_import_instance_before_process(self, import_instance):
        if self.language:
            import_instance.set_language(self.language)

        if isinstance(import_instance, ImportPropertyInstance):
            self.update_property_import_instance(import_instance)
        elif isinstance(import_instance, ImportProductPropertiesRuleInstance):
            self.update_product_rule_import_instance(import_instance)
        elif isinstance(import_instance, ImportProductInstance):
            self.update_product_import_instance(import_instance)

    def update_property_import_instance(self, instance): pass
    def update_property_select_value_import_instance(self, instance, log_instance): pass
    def update_product_rule_import_instance(self, instance): pass
    def update_product_import_instance(self, instance): pass

    @handle_import_exception
    def generic_single_process(self, step_name, data, struct_method, final_data_method,import_cls, log_method, extra_params=None, add_data_to_log_method=False):
        # Prepare log and final data
        log_instance = struct_method(data)
        final_data = final_data_method(log_instance)
        # Instantiate import
        params = {'import_process': self.import_process}
        if extra_params:
            params.update(extra_params)

        import_instance = import_cls(final_data, **params)
        self.update_import_instance_before_process(import_instance)

        # Process record
        import_instance.process()
        # Update progress and log
        self.update_percentage()

        if add_data_to_log_method:
            log_method(log_instance, import_instance, data)
        else:
            log_method(log_instance, import_instance)

    def import_products_process(self):

        for product_data in self.get_products_data():
            self.generic_single_process(
                step_name='import_products_process',
                data=product_data,
                struct_method=self.get_structured_product_data,
                final_data_method=self.get_final_product_data_from_log,
                import_cls=ImportProductInstance,
                log_method=self.update_product_log_instance,
            )

    def import_properties_process(self):
        for property_data in self.get_properties_data():
            self.generic_single_process(
                step_name='import_properties_process',
                data=property_data,
                struct_method=self.get_structured_property_data,
                final_data_method=self.get_final_property_data_from_log,
                import_cls=ImportPropertyInstance,
                log_method=self.update_property_log_instance,
            )

    def get_select_value_property_instance(self, log_instance, value_data):
        return None

    @handle_import_exception
    def process_single_select_value(self, value_data):
        log_instance = self.get_structured_select_value_data(value_data)
        final_data = self.get_final_select_value_data_from_log(log_instance)
        import_instance = ImportPropertySelectValueInstance(
            final_data,
            self.import_process,
            property=self.get_select_value_property_instance(log_instance, value_data)
        )
        self.update_property_select_value_import_instance(import_instance, value_data)
        import_instance.process()
        self.update_percentage()
        self.update_select_value_log_instance(log_instance, import_instance)

    def import_select_values_process(self):
        for value_data in self.get_select_values_data():
            self.process_single_select_value(value_data)

    def import_rules_process(self):
        for rule_data in self.get_rules_data():
            self.generic_single_process(
                step_name='import_rules_process',
                data=rule_data,
                struct_method=self.get_structured_rule_data,
                final_data_method=self.get_final_rule_data_from_log,
                import_cls=ImportProductPropertiesRuleInstance,
                log_method=self.update_rule_log_instance,
                add_data_to_log_method=True
            )

    def prepare_import_process(self):
        """
        Preparation for the import process
        """
        pass

    def process_completed(self):
        pass
    
    def set_broken_records(self):

        if len(self._broken_records) > 0:
            self.import_process.broken_records = self._broken_records
            self.import_process.save(update_fields=['broken_records'])

    def send_reports(self):

        reports = ImportReport.objects.filter(import_process=self.import_process)
        if not reports:
            return

        context_base = {
            "import_obj": self.import_process,
        }

        if self.import_process.skip_broken_records:
            context_base["errors"] = self.import_process.get_cleaned_errors_from_broken_records()

        company_lang = getattr(self.import_process.multi_tenant_company, "language", "en")

        for report in reports:
            recipient_emails = list(report.users.values_list("username", flat=True))
            recipient_emails.extend(report.external_emails or [])

            for email in recipient_emails:
                language = company_lang
                user_qs = report.users.filter(username=email)
                if user_qs.exists():
                    language = user_qs.first().language

                context = context_base.copy()
                fac = SendImportReportEmailFactory(email=email, language=language, context=context)
                fac.run()

    @timeit_and_log(logger, "importing products")
    def run(self):
        self.prepare_import_process()
        self.calculate_percentage()
        self.strat_process()

        try:
            if self.import_properties:
                self.import_properties_process()

            if self.import_select_values:
                self.import_select_values_process()

            if self.import_rules:
                self.import_rules_process()

            if self.import_products:
                self.import_products_process()

            self.mark_success()

        except Exception as e:
            self.mark_failure()

            raise

        finally:
            self.process_completed()
            
            if self.import_process.skip_broken_records:
                self.set_broken_records()

            self.send_reports()


class AsyncProductImportMixin(ImportMixin):
    """Variant of ImportMixin that dispatches each product to an async task."""

    async_task = None  # db_task that processes a single record

    def dispatch_task(self, data, is_last=False, updated_with=None):
        if not self.async_task:
            raise ValueError("async_task is not defined")

        safe_run_task(
            self.async_task,
            self.import_process.id,
            self.sales_channel.id,
            data,
            is_last,
            updated_with,
        )

    def run(self):
        self.prepare_import_process()
        self.strat_process()

        self.import_process.total_records = self.get_total_instances()
        self.import_process.processed_records = 0
        self.import_process.percentage = 0
        self.import_process.save(update_fields=["total_records", "processed_records", "percentage", "status"])

        self.total_import_instances_cnt = self.import_process.total_records
        self.set_threshold_chunk()

        item = None
        idx = 0

        for idx, item in enumerate(self.get_products_data(), start=1):

            update_delta = None
            if idx % self._threshold_chunk == 0:
                update_delta = self._threshold_chunk

            self.dispatch_task(item, is_last=False, updated_with=update_delta)

        if item:
            # we will import the last instance twice but we will make it work with both generators and list using
            # self.get_products_data() without needing to adapt the api wrapper to get which one is last
            # and relying it on self.get_total_instances() is dangerous (ex a product is deleted or created while
            # processing when we use generator and this doesn't match anymore)
            update_delta = idx % self._threshold_chunk if idx % self._threshold_chunk != 0 else None
            self.dispatch_task(item, is_last=True, updated_with=update_delta)
