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
