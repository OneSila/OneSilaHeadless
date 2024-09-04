'''
        mutation = """
            mutation createSalesPrice($data: SalesPriceInput!) {
                createSalesPrice(data: $data) {
                  id
                  rrp
                  price
                }
              }
        """
        resp = self.strawberry_test_client(
            asserts_errors=False,
            query=mutation,
            variables={'data': {
                "product": {"id": simple_product_id},
                "currency": {"id": currency_id}

            }}
        )
'''

INVENTORY_MOVEMENT_CREATE = """
    mutation createInventoryMovement($data: InventoryMovementInput!){
      createInventoryMovement(data: $data){
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
"""
