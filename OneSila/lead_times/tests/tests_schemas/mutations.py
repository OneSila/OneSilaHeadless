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
