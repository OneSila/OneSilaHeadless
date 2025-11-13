SHEIN_PROPERTY_FILTER_BY_SALES_CHANNEL = """
query ($salesChannel: GlobalID!) {
  sheinProperties(filters: {salesChannel: {id: {exact: $salesChannel}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

SHEIN_PROPERTY_SELECT_VALUE_FILTER_BY_PROPERTY = """
query ($property: GlobalID!) {
  sheinPropertySelectValues(filters: {remoteProperty: {id: {exact: $property}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

SHEIN_PRODUCT_TYPE_FILTER_BY_CATEGORY = """
query ($categoryId: String!) {
  sheinProductTypes(filters: {categoryId: {exact: $categoryId}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

SHEIN_PRODUCT_TYPE_ITEM_FILTER_BY_PROPERTY = """
query ($property: GlobalID!) {
  sheinProductTypeItems(filters: {property: {id: {exact: $property}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

SHEIN_INTERNAL_PROPERTY_OPTION_FILTER_BY_INTERNAL_PROPERTY = """
query ($internalProperty: GlobalID!) {
  sheinInternalPropertyOptions(filters: {internalProperty: {id: {exact: $internalProperty}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

SHEIN_CATEGORY_FILTER_BY_SITE_AND_LEAF = """
query ($siteRemoteId: String!) {
  sheinCategories(
    filters: {
      siteRemoteId: {exact: $siteRemoteId}
      isLeaf: {exact: true}
    }
  ) {
    edges {
      node {
        id
        remoteId
        siteRemoteId
        parentRemoteId
        isLeaf
      }
    }
  }
}
"""
