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

PRODUCTS_ASSIGNED_TO_VIEW_QUERY = """
query Products($view: ID!) {
  products(filters: {assignedToSalesChannelView: $view}) {
    edges { node { id } }
  }
}
"""

PRODUCTS_NOT_ASSIGNED_TO_VIEW_QUERY = """
query Products($view: ID!) {
  products(filters: {notAssignedToSalesChannelView: $view}) {
    edges { node { id } }
  }
}
"""
