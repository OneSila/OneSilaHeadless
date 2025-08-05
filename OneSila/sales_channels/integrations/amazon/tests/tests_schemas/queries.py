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
