create_leadtime_for_shippingaddress = """
    mutation($shippingid: GlobalID!, $leadtimeid: GlobalID!) {
      createLeadTimeForShippingaddress(
        data: {shippingaddress: {id: $shippingid}, leadtime: {id: $leadtimeid}}
      ) {
        id
        leadtime {
          id
        }
        shippingaddress {
          id
        }
      }
    }
"""

create_lead_time_product_outofstock = """
    mutation($productid: GlobalID!, $leadtimeid: GlobalID!) {
      createLeadTimeProductOutOfStock(
        data: {product: {id: $productid}, leadtimeOutofstock: {id: $leadtimeid}}
      ) {
        id
        leadtimeOutofstock {
          id
        }
        product {
          id
        }
      }
    }
"""
