INVENTORY_MOVEMENTS_QUERY = """
query inventoryMovements{
  inventoryMovements{
    edges{
      node {
        quantity
        notes
        product {
          id
        }
        movementFrom {
                    ... on InventoryType {
                id
                }
                ... on PurchaseOrderType {
            id
                  }
        }
        movementTo {
                    ... on InventoryType {
                id
                }
                ... on PackageType {
            id
                  }
        }
      }
    }
  }
}
"""
