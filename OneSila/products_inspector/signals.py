from django.db.models.signals import ModelSignal

inspector_block_refresh = ModelSignal(use_caching=True)

# General signals for the inspector
inspector_missing_info_detected = ModelSignal(use_caching=True)  # True
inspector_missing_info_resolved = ModelSignal(use_caching=True)  # False
inspector_missing_optional_info_detected = ModelSignal(use_caching=True)  # True
inspector_missing_optional_info_resolved = ModelSignal(use_caching=True)  # False

# signals for HAS_IMAGES
inspector_has_images_failed = ModelSignal(use_caching=True)
inspector_has_images_success = ModelSignal(use_caching=True)

# signals for missing prices
inspector_missing_prices_failed = ModelSignal(use_caching=True)
inspector_missing_prices_success = ModelSignal(use_caching=True)

# signals for missing manufacturable pieces
inspector_inactive_pieces_failed = ModelSignal(use_caching=True)
inspector_inactive_pieces_success = ModelSignal(use_caching=True)

# signals for missing bundle items
inspector_inactive_bundle_items_failed = ModelSignal(use_caching=True)
inspector_inactive_bundle_items_success = ModelSignal(use_caching=True)

# signals for missing variations
inspector_missing_variation_failed = ModelSignal(use_caching=True)
inspector_missing_variation_success = ModelSignal(use_caching=True)

# signals for missing bundle items
inspector_missing_bundle_items_failed = ModelSignal(use_caching=True)
inspector_missing_bundle_items_success = ModelSignal(use_caching=True)

# signals for missing bill of materials
inspector_missing_bill_of_materials_failed = ModelSignal(use_caching=True)
inspector_missing_bill_of_materials_success = ModelSignal(use_caching=True)

# signals for missing supplier products
inspector_missing_supplier_products_failed = ModelSignal(use_caching=True)
inspector_missing_supplier_products_success = ModelSignal(use_caching=True)

# signals for missing ean code
inspector_missing_ean_code_failed = ModelSignal(use_caching=True)
inspector_missing_ean_code_success = ModelSignal(use_caching=True)

# signals for missing product type
inspector_missing_product_type_failed = ModelSignal(use_caching=True)
inspector_missing_product_type_success = ModelSignal(use_caching=True)

# signals for properties requirements inspector
inspector_missing_required_properties_failed = ModelSignal(use_caching=True)
inspector_missing_required_properties_success = ModelSignal(use_caching=True)

inspector_missing_optional_properties_failed = ModelSignal(use_caching=True)
inspector_missing_optional_properties_success = ModelSignal(use_caching=True)

# signals for supplier prices
inspector_missing_supplier_prices_failed = ModelSignal(use_caching=True)
inspector_missing_supplier_prices_success = ModelSignal(use_caching=True)

# signals for missing stock
inspector_missing_stock_failed = ModelSignal(use_caching=True)
inspector_missing_stock_success = ModelSignal(use_caching=True)

# signals for missing lead time out of stock
inspector_missing_lead_time_failed = ModelSignal(use_caching=True)
inspector_missing_lead_time_success = ModelSignal(use_caching=True)

# signals for missing price for manual pricelists
inspector_missing_manual_pricelist_override_failed = ModelSignal(use_caching=True)
inspector_missing_manual_pricelist_override_success = ModelSignal(use_caching=True)

# signals for mismatch variations product type
inspector_variation_mismatch_product_type_failed = ModelSignal(use_caching=True)
inspector_variation_mismatch_product_type_success = ModelSignal(use_caching=True)

# signals for mismatch items product type
inspector_items_mismatch_product_type_failed = ModelSignal(use_caching=True)
inspector_items_mismatch_product_type_success = ModelSignal(use_caching=True)

# signals for mismatch bom product type
inspector_bom_mismatch_product_type_failed = ModelSignal(use_caching=True)
inspector_bom_mismatch_product_type_success = ModelSignal(use_caching=True)

# signals for missing info for items
inspector_items_missing_mandatory_information_failed = ModelSignal(use_caching=True)
inspector_items_missing_mandatory_information_success = ModelSignal(use_caching=True)

# signals for missing info for variations
inspector_variations_missing_mandatory_information_failed = ModelSignal(use_caching=True)
inspector_variations_missing_mandatory_information_success = ModelSignal(use_caching=True)

# signals for missing info for bom
inspector_bom_missing_mandatory_information_failed = ModelSignal(use_caching=True)
inspector_bom_missing_mandatory_information_success = ModelSignal(use_caching=True)

# signals for duplicate variations
inspector_duplicate_variations_failed = ModelSignal(use_caching=True)
inspector_duplicate_variations_success = ModelSignal(use_caching=True)

# signals for configurable product with wrong rule
inspector_non_configurable_rule_success = ModelSignal(use_caching=True)
inspector_non_configurable_rule_failed = ModelSignal(use_caching=True)

# signals for amazon issues
inspector_amazon_validation_issues_failed = ModelSignal(use_caching=True)
inspector_amazon_validation_issues_success = ModelSignal(use_caching=True)
inspector_amazon_remote_issues_failed = ModelSignal(use_caching=True)
inspector_amazon_remote_issues_success = ModelSignal(use_caching=True)
