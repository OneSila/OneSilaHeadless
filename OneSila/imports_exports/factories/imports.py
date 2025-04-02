from imports_exports.factories.products import ImportProductInstance
from imports_exports.factories.properties import ImportProductPropertiesRuleInstance, ImportPropertySelectValueInstance, \
    ImportPropertyInstance
from imports_exports.models import Import
import traceback
import math

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

    def import_products_process(self):
        for product_data in self.get_products_data():
            log_instance = self.get_structured_product_data(product_data)
            import_instance = ImportProductInstance(self.get_final_product_data_from_log(log_instance), self.import_process)
            self.update_import_instance_before_process(import_instance)
            import_instance.process()
            self.update_percentage()
            self.update_product_log_instance(log_instance, import_instance)

    def import_properties_process(self):
        for property_data in self.get_properties_data():
            log_instance = self.get_structured_property_data(property_data)
            import_instance = ImportPropertyInstance(self.get_final_property_data_from_log(log_instance), self.import_process)
            self.update_import_instance_before_process(import_instance)
            import_instance.process()
            self.update_percentage()
            self.update_property_log_instance(log_instance, import_instance)

    def get_select_value_property_instance(self, log_instance, value_data):
        return None

    def import_select_values_process(self):
        for value_data in self.get_select_values_data():
            log_instance = self.get_structured_select_value_data(value_data)
            import_instance = ImportPropertySelectValueInstance(self.get_final_select_value_data_from_log(log_instance), self.import_process, property=self.get_select_value_property_instance(log_instance, value_data))
            self.update_property_select_value_import_instance(import_instance, value_data)
            import_instance.process()
            self.update_percentage()
            self.update_select_value_log_instance(log_instance, import_instance)

    def import_rules_process(self):
        for rule_data in self.get_rules_data():
            log_instance = self.get_structured_rule_data(rule_data)
            import_instance = ImportProductPropertiesRuleInstance(self.get_final_rule_data_from_log(log_instance), self.import_process)
            self.update_import_instance_before_process(import_instance)
            import_instance.process()
            self.update_percentage()
            self.update_rule_log_instance(log_instance, import_instance, rule_data)

    def prepare_import_process(self):
        """
        Preparation for the import process
        """
        pass

    def process_completed(self):
        pass

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

        finally:
            self.process_completed()