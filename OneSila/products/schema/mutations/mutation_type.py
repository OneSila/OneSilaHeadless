from .fields import create_product, create_supplier_product
from ..types.types import ProductType, BundleProductType, ConfigurableProductType, \
    SimpleProductType, ProductTranslationType, ConfigurableVariationType, \
    BundleVariationType, ManufacturableProductType, DropshipProductType, SupplierProductType, BillOfMaterialType, SupplierPricesType
from ..types.input import ProductInput, BundleProductInput, ConfigurableProductInput, \
    SimpleProductInput, ProductTranslationInput, ConfigurableVariationInput, \
    BundleVariationInput, ProductPartialInput, ConfigurableProductPartialInput, \
    BundleProductPartialInput, SimpleProductPartialInput, \
    ProductTranslationPartialInput, ConfigurableVariationPartialInput, \
    BundleVariationPartialInput, ManufacturableProductInput, ManufacturableProductPartialInput, DropshipProductInput, DropshipProductPartialInput, \
    SupplierProductInput, SupplierProductPartialInput, BillOfMaterialInput, BillOfMaterialPartialInput, SupplierPricesPartialInput, SupplierPricesInput
from core.schema.core.mutations import create, update, delete, type, List


@type(name="Mutation")
class ProductsMutation:
    create_product: ProductType = create_product()
    create_products: List[ProductType] = create(ProductInput)
    update_product: ProductType = update(ProductPartialInput)
    delete_product: ProductType = delete()
    delete_products: List[ProductType] = delete()

    create_bundle_product: BundleProductType = create(BundleProductInput)
    create_bundle_products: List[BundleProductType] = create(BundleProductInput)
    update_bundle_product: BundleProductType = update(BundleProductPartialInput)
    delete_bundle_product: BundleProductType = delete()
    delete_bundle_products: List[BundleProductType] = delete()

    create_configurable_product: ConfigurableProductType = create(ConfigurableProductInput)
    create_configurable_products: List[ConfigurableProductType] = create(ConfigurableProductInput)
    update_configurable_product: ConfigurableProductType = update(ConfigurableProductPartialInput)
    delete_configurable_product: ConfigurableProductType = delete()
    delete_configurable_products: List[ConfigurableProductType] = delete()

    create_simple_product: SimpleProductType = create(SimpleProductInput)
    create_simple_products: List[SimpleProductType] = create(SimpleProductInput)
    update_simple_product: SimpleProductType = update(SimpleProductPartialInput)
    delete_simple_product: SimpleProductType = delete()
    delete_simple_products: List[SimpleProductType] = delete()

    create_product_translation: ProductTranslationType = create(ProductTranslationInput)
    create_product_translations: List[ProductTranslationType] = create(ProductTranslationInput)
    update_product_translation: ProductTranslationType = update(ProductTranslationPartialInput)
    delete_product_translation: ProductTranslationType = delete()
    delete_product_translations: List[ProductTranslationType] = delete()

    create_configurable_variation: ConfigurableVariationType = create(ConfigurableVariationInput)
    create_configurable_variations: List[ConfigurableVariationType] = create(ConfigurableVariationInput)
    update_configurable_variation: ConfigurableVariationType = update(ConfigurableVariationPartialInput)
    delete_configurable_variation: ConfigurableVariationType = delete()
    delete_configurable_variations: List[ConfigurableVariationType] = delete()

    create_bundle_variation: BundleVariationType = create(BundleVariationInput)
    create_bundle_variations: List[BundleVariationType] = create(BundleVariationInput)
    update_bundle_variation: BundleVariationType = update(BundleVariationPartialInput)
    delete_bundle_variation: BundleVariationType = delete()
    delete_bundle_variations: List[BundleVariationType] = delete()

    create_manufacturable_product: ManufacturableProductType = create(ManufacturableProductInput)
    create_manufacturable_products: List[ManufacturableProductType] = create(ManufacturableProductInput)
    update_manufacturable_product: ManufacturableProductType = update(ManufacturableProductPartialInput)
    delete_manufacturable_product: ManufacturableProductType = delete()
    delete_manufacturable_products: List[ManufacturableProductType] = delete()

    create_dropship_product: DropshipProductType = create(DropshipProductInput)
    create_dropship_products: List[DropshipProductType] = create(DropshipProductInput)
    update_dropship_product: DropshipProductType = update(DropshipProductPartialInput)
    delete_dropship_product: DropshipProductType = delete()
    delete_dropship_products: List[DropshipProductType] = delete()

    create_supplier_product: SupplierProductType = create_supplier_product()
    create_supplier_products: List[SupplierProductType] = create(SupplierProductInput)
    update_supplier_product: SupplierProductType = update(SupplierProductPartialInput)
    delete_supplier_product: SupplierProductType = delete()
    delete_supplier_products: List[SupplierProductType] = delete()

    create_bill_of_material: BillOfMaterialType = create(BillOfMaterialInput)
    create_bills_of_material: List[BillOfMaterialType] = create(BillOfMaterialInput)
    update_bill_of_material: BillOfMaterialType = update(BillOfMaterialPartialInput)
    delete_bill_of_material: BillOfMaterialType = delete()
    delete_bills_of_material: List[BillOfMaterialType] = delete()

    create_supplier_price: SupplierPricesType = create(SupplierPricesInput)
    update_supplier_price: SupplierPricesType = update(SupplierPricesPartialInput)
    delete_supplier_price: SupplierPricesType = delete()
