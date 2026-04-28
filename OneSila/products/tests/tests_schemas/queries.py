SIMPLE_PRODUCT_SKU_FILTER = """
    query simpleProducts($sku: String!){
      simpleProducts(filters: {sku: {exact: $sku}}) {
        edges {
          node {
            id
          }
        }
      }
    }
"""

PRODUCT_SEARCH = """
query products($search: String!) {
  products(filters:{search:$search}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

PRODUCT_EXCLUDE_DEMO_DATA = """
query products($excludeDemoData: Boolean!) {
  products(filters:{excludeDemoData:$excludeDemoData}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

PRODUCTS_FILTER_BY_SKU = """
query products($sku: String!) {
  products(filters: {sku: {exact: $sku}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_TYPE = """
query products($type: String!) {
  products(filters: {type: {exact: $type}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_EXCLUDE_TYPE = """
query products($type: String!) {
  products(filters: {NOT: {type: {exact: $type}}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_ACTIVE = """
query products($active: Boolean!) {
  products(filters: {active: {exact: $active}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_ALLOW_BACKORDER = """
query products($allowBackorder: Boolean!) {
  products(filters: {allowBackorder: {exact: $allowBackorder}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_VAT_RATE = """
query products($rate: Int!) {
  products(filters: {vatRate: {rate: {exact: $rate}}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_CREATED_AT = """
query products($createdAfter: DateTime!) {
  products(filters: {createdAt: {gte: $createdAfter}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_UPDATED_AT = """
query products($updatedAfter: DateTime!) {
  products(filters: {updatedAt: {gte: $updatedAfter}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_HAS_EAN_CODES = """
query products($hasEanCodes: Boolean!) {
  products(filters: {hasEanCodes: $hasEanCodes}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_HAS_ALIAS_PRODUCTS = """
query products($hasAliasProducts: Boolean!) {
  products(filters: {hasAliasProducts: $hasAliasProducts}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_HAS_MULTIPLE_CONFIGURABLE_PARENTS = """
query products($hasMultipleConfigurableParents: Boolean!) {
  products(filters: {hasMultipleConfigurableParents: $hasMultipleConfigurableParents}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_VARIATION_OF_PRODUCT_ID = """
query products($productId: String!) {
  products(filters: {variationOfProductId: $productId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_IS_MULTIPLE_PARENT = """
query products($isMultipleParent: Boolean!) {
  products(filters: {isMultipleParent: $isMultipleParent}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_ALIAS_PARENT = """
query products($parentId: GlobalID!) {
  products(filters: {aliasParentProduct: {id: {exact: $parentId}}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_HAS_PRICES_FOR_CURRENCY = """
query products($currencyId: String!) {
  products(filters: {hasPricesForCurrency: $currencyId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_MISSING_PRICES_FOR_CURRENCY = """
query products($currencyId: String!) {
  products(filters: {missingPricesForCurrency: $currencyId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_HAS_PRICE_LIST = """
query products($priceListId: String!) {
  products(filters: {hasPriceList: $priceListId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_MISSING_PRICE_LIST = """
query products($priceListId: String!) {
  products(filters: {missingPriceList: $priceListId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_CREATED_AT_RANGE = """
query products($range: String!) {
  products(filters: {createdAtRange: $range}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_UPDATED_AT_RANGE = """
query products($range: String!) {
  products(filters: {updatedAtRange: $range}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_PRESENT_ON_STORE_SALES_CHANNEL = """
query products($salesChannelId: String!) {
  products(filters: {presentOnStoreSalesChannelId: $salesChannelId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_NOT_PRESENT_ON_STORE_SALES_CHANNEL = """
query products($salesChannelId: String!) {
  products(filters: {notPresentOnStoreSalesChannelId: $salesChannelId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_HAS_IMAGES_IN_SALES_CHANNEL = """
query products($salesChannelId: String!) {
  products(filters: {hasImagesInSalesChannel: $salesChannelId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_MISSING_IMAGES_IN_SALES_CHANNEL = """
query products($salesChannelId: String!) {
  products(filters: {missingImagesInSalesChannel: $salesChannelId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_HAS_DOCUMENTS_IN_SALES_CHANNEL = """
query products($salesChannelId: String!) {
  products(filters: {hasDocumentsInSalesChannel: $salesChannelId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_MISSING_DOCUMENTS_IN_SALES_CHANNEL = """
query products($salesChannelId: String!) {
  products(filters: {missingDocumentsInSalesChannel: $salesChannelId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_WITH_WORKFLOW_STATE_ID_QUERY = """
query products($id: String!) {
  products(filters: {workflowStateId: $id}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_HAS_VIDEOS_IN_SALES_CHANNEL = """
query products($salesChannelId: String!) {
  products(filters: {hasVideosInSalesChannel: $salesChannelId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_MISSING_VIDEOS_IN_SALES_CHANNEL = """
query products($salesChannelId: String!) {
  products(filters: {missingVideosInSalesChannel: $salesChannelId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_AMAZON_BROWSER_NODE = """
query products($amazonBrowseNodeId: String!) {
  products(filters: {amazonBrowserNodeId: $amazonBrowseNodeId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_EXCLUDE_AMAZON_BROWSER_NODE = """
query products($amazonBrowseNodeId: String!) {
  products(filters: {excludeAmazonBrowserNodeId: $amazonBrowseNodeId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_EBAY_PRODUCT_CATEGORY = """
query products($ebayCategoryId: String!) {
  products(filters: {ebayProductCategoryId: $ebayCategoryId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_EXCLUDE_EBAY_PRODUCT_CATEGORY = """
query products($ebayCategoryId: String!) {
  products(filters: {excludeEbayProductCategoryId: $ebayCategoryId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_SHEIN_PRODUCT_CATEGORY = """
query products($sheinCategoryId: String!) {
  products(filters: {sheinProductCategoryId: $sheinCategoryId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_EXCLUDE_SHEIN_PRODUCT_CATEGORY = """
query products($sheinCategoryId: String!) {
  products(filters: {excludeSheinProductCategoryId: $sheinCategoryId}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_MISSING_REQUIRED_INFORMATION = """
query products {
  products(filters: {inspector: {hasMissingInformation: {exact: true}}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_MISSING_INFORMATION = """
query products {
  products(filters: {inspector: {hasAnyMissingInformation: true}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_INSPECTOR_NOT_SUCCESSFULLY_CODE_ERROR = """
query products($errorCode: String!) {
  products(filters: {inspectorNotSuccessfullyCodeError: $errorCode}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_EXCLUDE_INSPECTOR_NOT_SUCCESSFULLY_CODE_ERROR = """
query products($errorCode: String!) {
  products(filters: {NOT: {inspectorNotSuccessfullyCodeError: $errorCode}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_CONTENT_FIELD_IN_VIEW = """
query products($contentViewKey: String!, $field: ContentField!) {
  products(filters: {contentFieldInView: {contentViewKey: $contentViewKey, field: $field}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_FILTER_BY_MISSING_CONTENT_FIELD_IN_VIEW = """
query products($contentViewKey: String!, $field: ContentField!) {
  products(filters: {NOT: {contentFieldInView: {contentViewKey: $contentViewKey, field: $field}}}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_ASSIGNED_TO_VIEW_QUERY = """
query Products($view: String!) {
  products(filters: {assignedToSalesChannelViewId: $view}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_NOT_ASSIGNED_TO_VIEW_QUERY = """
query Products($view: String!) {
  products(filters: {notAssignedToSalesChannelViewId: $view}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_REJECTED_FOR_VIEW_QUERY = """
query Products($view: String!) {
  products(filters: {rejectedForSalesChannelViewId: $view}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_TODO_FOR_VIEW_QUERY = """
query Products($view: String!) {
  products(filters: {todoForSalesChannelViewId: $view}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_HAS_TODO_VIEW_QUERY = """
query Products($hasTodo: Boolean!) {
  products(filters: {hasTodoSalesChannelView: $hasTodo}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_REJECTED_VIEW_ASSIGN_SET_QUERY = """
query Products($sku: String!) {
  products(filters: {sku: {exact: $sku}}) {
    edges {
      node {
        id
        rejectedsaleschannelviewassignSet {
          id
          salesChannelView { id }
        }
      }
    }
  }
}
"""

PRODUCTS_WITH_VALUE_SELECT_IDS_QUERY = """
query Products($ids: [String!]!) {
  products(filters: {valueSelectIds: $ids}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_WITH_VALUE_SELECT_ID_QUERY = """
query Products($id: String!) {
  products(filters: {valueSelectId: $id}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_WITH_PROPERTY_ID_QUERY = """
query Products($id: String!) {
  products(filters: {propertyId: $id}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_WITH_NOT_PROPERTY_ID_QUERY = """
query Products($id: String!) {
  products(filters: {NOT: {propertyId: $id}}) {
    edges { node { id } }
  }
}
"""
