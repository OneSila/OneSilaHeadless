[![codecov](https://codecov.io/gh/OneSila/OneSilaHeadless/graph/badge.svg?token=URYTB56K2W)](https://codecov.io/gh/OneSila/OneSilaHeadless)

# OneSila Headless Backend

## Quickstart

Install dependencies:

```bash
virtualenv venv
source venv/bin/active

pip install -r requirements.txt
```

Create your local settings:

```bash
cp OneSila/settings/local_template.py OneSila/settings/local.py
```

And create a postgres db + set the settings in your local.py setting file.
Also add CORS settings to your local file.

```
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # check the right port from your frontend npm run dev.
]
```

Next, migrate your db:

```python
./manange.py migrate
```

## Viewing docs

Docs are housed inside of the docs folder.  You can view them easily by running `mkdocs serve` like so:

```bash
source venv/bin/active
mkdocs serve
# Now open: http://127.0.0.1:8000
```

## Graphql

Getting data out of - and putting in - is done using graphql.
eg, creating a company via (graphiql)[http://127.0.0.1:8080/graphql/]:

```graphql
mutation createCompany {
  createCompany(data: {name: "Company ltd"}) {
    id
    name
    multiTenantCompany{
      name
    }
  }
}
```

will yield:

```json
{
  "data": {
    "createCompany": {
      "id": "Q29tcGFueVR5cGU6OQ==",
      "name": "Company ltd",
      "multiTenantCompany": {
        "name": "Owner"
      }
    }
  }
}
```

You can also subscribe to it's updates:

```graphql
subscription companySubscriptionClass {
  company(pk: "Q29tcGFueVR5cGU6OQ==") {
    id
    name
    createdAt
    updatedAt
  }
}
```

will yield:
```json
{
  "data": {
    "company": {
      "id": "Q29tcGFueVR5cGU6OQ==",
      "name": "Company ltd",
      "createdAt": "2023-10-03T16:11:21.900275+00:00",
      "updatedAt": "2023-10-03T16:11:21.900310+00:00"
    }
  }
}
```

## Running tests

Runings tests, including coverage:

```bash
coverage run --source='.' manage.py test
```

To see the results

```bash
coverage report -m
```

Or with html

```bash
coverage html
```

## Supported Currencies

The list of available currencies can be found in `currencies/currencies.py`.
Each entry contains the ISO code, human readable name and symbol. Recent
additions include codes such as `AFN` (Afghan Afghani) and `CHF` (Swiss Franc).
