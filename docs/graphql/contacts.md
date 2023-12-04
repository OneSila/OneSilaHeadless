# Contacts

The contacts app is where you can find all contacts related to the company except for user information.

That means:
- Customers
- Suppliers
- Partners
- Influencers
- Internal Companies

All of these are also available simply as Company.

!!!tip:
    Internal Companies are for external communication and have nothing to do with the MultiTenantCompany.


Each of these companies can contain:
- Person / People
- Address
    - ShippingAddress
    - InvoicingAddress


## Internal structure

Internally, Company- and Address-models are known as ProxyModels.  That means that the real models are "Company", and "Address".  All the others like Customers, Suppliers, ShippingAddresses, etc are convenient wrappers.

Why is this important?  Because Graphql will not allow you to fetch a Customer with the id you received from Company. This is due to some internal mechanics.

Why is that?  Proxy-models are a wrapper, and graphql encodes the model-type inside of the id but cannot destinguish between the two.

!!!tip:
    Don't mix up the ids from eg Customer and Company.  Even though they are both the same, graphql/django cannot detect that. Respect the type of your id.


## Querie example:
```graphql
{companies{
  edges{
    node{
      id
      isSupplier
    }
  }
}}
```
