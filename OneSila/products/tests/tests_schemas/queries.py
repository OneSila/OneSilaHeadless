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
query simpleProducts($search: String!) {
  simpleProducts(filters:{search:$search}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

PRODUCT_EXCLUDE_DEMO_DATA = """
query simpleProducts($excludeDemoData: Boolean!) {
  simpleProducts(filters:{excludeDemoData:$excludeDemoData}) {
    edges {
      node {
        id
      }
    }
  }
}
"""
