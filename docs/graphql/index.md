# Getting Started

Querying graphql is based on the strawberry library.  You can find some samples below.

## Exploring the playground.

Once you have setup the backend, you can easily run the system locally for testing.  In order to do this, run:

```
source venv/bin/activate
cd OneSila
./manage.py runserver 127.0.0.1:8080
```

This will give your system access to (http://127.0.0.1:8080/graphql)[http://127.0.0.1:8080/graphql]. In this location you can explore / test all queries, mutations and subscriptions available.  Including the fields, field requirements and return options available.


## Query Single result

```graphql
{
  company(id: "Q29tcGFueVR5cGU6Mg==") {
    id
  }
}
```

## Subscribing to single result

```graphql
subscription{
  company(pk: "Q29tcGFueVR5cGU6Mg==") {
    id
  }
}
```


## List Queries

### Pagination:
https://strawberry.rocks/docs/guides/pagination/cursor-based

A default page-size seems to be 100 items - unless overriden with "first"


```graphql
query companies {
  companies(first:2) {
    edges {
      node {
        name
        id
      }
    }
    pageInfo {
      hasNextPage
      startCursor
      endCursor
    }
  }
}
```

or on a local machine with some random companies, you can get the next page like so:

```graphql
query companies {
  companies(first:2, after: "YXJyYXljb25uZWN0aW9uOjE=") {
    edges {
      node {
        name
        id
      }
    }
    pageInfo {
      hasNextPage
      startCursor
      endCursor
    }
  }
}
```

First, you can interpret as you page-size (with a maximum of 100).


### filtering

```graphql
query companies{
  companies(filters:{name:{contains:"test"}}) {
    edges {
      node {
        name
        id
      }
    }
  }
}
```


### ordering

```graphql
query companies{
  companies(order:{name:ASC}) {
    edges {
      node {
        name
        id
      }
    }
  }
}
```

### Combing things:

```graphql
query companies{
  companies(filters:{name:{contains:"test"}}, order:{name:ASC}) {
    edges {
      node {
        name
        id
      }
    }
  }
}
```
