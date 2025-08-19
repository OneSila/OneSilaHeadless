AMAZON_PRODUCT_FILTER_BY_LOCAL_INSTANCE = """
query ($localInstance: GlobalID!) {
  amazonProducts(filters: {localInstance: {id: {exact: $localInstance}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

AMAZON_PRODUCT_WITH_ISSUES = """
query ($id: GlobalID!) {
  amazonProduct(id: $id) {
    id
    issues {
      code
      message
      severity
      isValidationIssue
    }
  }
}
"""

AMAZON_PRODUCT_PROPERTY_FILTER_BY_LOCAL_INSTANCE = """
query ($localInstance: GlobalID!) {
  amazonProductProperties(filters: {localInstance: {id: {exact: $localInstance}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

AMAZON_PRODUCT_PROPERTY_FILTER_BY_REMOTE_SELECT_VALUE = """
query ($remoteSelectValue: GlobalID!) {
  amazonProductProperties(filters: {remoteSelectValue: {id: {exact: $remoteSelectValue}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

AMAZON_PRODUCT_PROPERTY_FILTER_BY_REMOTE_PRODUCT = """
query ($remoteProduct: GlobalID!) {
  amazonProductProperties(filters: {remoteProduct: {id: {exact: $remoteProduct}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

AMAZON_MERCHANT_ASIN_FILTER_BY_PRODUCT = """
query ($product: GlobalID!) {
  amazonMerchantAsins(filters: {product: {id: {exact: $product}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

AMAZON_GTIN_EXEMPTION_FILTER_BY_PRODUCT = """
query ($product: GlobalID!) {
  amazonGtinExemptions(filters: {product: {id: {exact: $product}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

AMAZON_VARIATION_THEME_FILTER_BY_PRODUCT = """
query ($product: GlobalID!) {
  amazonVariationThemes(filters: {product: {id: {exact: $product}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""
