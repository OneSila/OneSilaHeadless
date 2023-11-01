# Known issues

## Graphql single object fetching for proxy-models

Fetching a single object suffers from returning an incorrect object type when the model is
a proxy model, eg Customer vs Company.  Example:

```graphql
query customers {
  customers(filters:{id: "Q29tcGFueVR5cGU6NA=="}) {
    edges {
      node {
        id
        name
        __typename
      }
    }
  }
}
```

Yet, using the filter-approach yields the correct response.

```graphql
query customers {
  companies(filters:{id: {exact:"Q29tcGFueVR5cGU6NA=="}}) {
    edges {
      node {
        id
        name
        __typename
      }
    }
  }
}
```

## Subscriptions not working

The subscriptions are setup, but at present not working yet.
Why?  It's awaiting the subscription-branch to be pushed to strawberry-django.
You can find the branch here: https://github.com/sdobbelaere/strawberry-graphql-django/tree/subscriptions
