ADDRESS_QUERY = """
    query addresses {
      addresses {
        edges {
          node {
            id
            fullAddress
          }
        }
        totalCount
      }
    }
"""

COMPANIES_QUERY = """
    query companies {
      companies {
        edges {
          node {
            id
          }
        }
        totalCount
      }
    }
"""

COMPANY_GET_QUERY = """
    query company($id: GlobalID!) {
        company(id: $id) {
            id
            name
            __typename
        }
    }
"""

COMPANY_LIST_FILTER_FRONTEND = """
query Companies($first: Int, $last: Int, $after: String, $before: String, $order: CompanyOrder, $filter: CompanyFilter) {
  companies(first: $first, last: $last, after: $after, before: $before, order: $order, filters: $filter) {
    edges {
      node {
        id
        name
        phone
        email
        language
        country
        currency {
          id
          isoCode
        }
      }
      cursor
    }
    totalCount
    pageInfo {
      endCursor
      startCursor
      hasNextPage
      hasPreviousPage
    }
  }
}
"""
