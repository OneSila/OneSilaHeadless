from .fields import create_product, create_supplier_product
from ..types.types import ProductType, BundleProductType, UmbrellaProductType, \
    SimpleProductType, ProductTranslationType, UmbrellaVariationType, \
    BundleVariationType, ManufacturableProductType, DropshipProductType, SupplierProductType, BillOfMaterialType, SupplierPricesType
from ..types.input import ProductInput, BundleProductInput, UmbrellaProductInput, \
    SimpleProductInput, ProductTranslationInput, UmbrellaVariationInput, \
    BundleVariationInput, ProductPartialInput, UmbrellaProductPartialInput, \
    BundleProductPartialInput, SimpleProductPartialInput, \
    ProductTranslationPartialInput, UmbrellaVariationPartialInput, \
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

    create_umbrella_product: UmbrellaProductType = create(UmbrellaProductInput)
    create_umbrella_products: List[UmbrellaProductType] = create(UmbrellaProductInput)
    update_umbrella_product: UmbrellaProductType = update(UmbrellaProductPartialInput)
    delete_umbrella_product: UmbrellaProductType = delete()
    delete_umbrella_products: List[UmbrellaProductType] = delete()

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

    create_umbrella_variation: UmbrellaVariationType = create(UmbrellaVariationInput)
    create_umbrella_variations: List[UmbrellaVariationType] = create(UmbrellaVariationInput)
    update_umbrella_variation: UmbrellaVariationType = update(UmbrellaVariationPartialInput)
    delete_umbrella_variation: UmbrellaVariationType = delete()
    delete_umbrella_variations: List[UmbrellaVariationType] = delete()

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
