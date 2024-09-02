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
                    ... on InventoryLocationType {
                id
                }
                ... on PurchaseOrderType {
            id
                  }
        }
        movementTo {
                    ... on InventoryLocationType {
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
