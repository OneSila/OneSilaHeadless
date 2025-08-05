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
