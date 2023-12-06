# Users and Multitenancy

The OneSila platform is based on a single database, single schema approach with shared models.
These shared models, all have a field company called `multi_tenant_company`.

This means that all data needs to be assigned to a given multi_tenant_company.  If you would skip
this step, the data would be lost to that user, or potentially shared with all users.

To understand how this is structured, take a look at [the model docs](developers/creating-new-apps.html)

## User Registration

For user registration, there has been a mutation created called `registerUser` and can be called with following query:

```graphql
mutation{
  registerUser(data:{username:"my@mail.com", password: "My123!Pass", language: "nl"}){
		username
  }
}
```

All of the fields in the mutation shown are required.
Note that the username is actually an emailfield.

Once the user has been registered, you are able to provide more information using the user update mutation.

```graphql
mutation {
  updateMe(data: {isActive: true}) {
    avatarResized {
      name
    }
  }
}
```

For a complete overview of all available fields, go explore the Graphql playground.


## Company Registration

Once a user has been registered, you must create the company.  Without the MultiTenantCompany, nothing would work as all data is assigned to the company.  The user is mereley the conduit.

The registration mutation looks like:

```graphql
mutation {
  registerMyMultiTenantCompany(
    data: {name: "company name", country: "BE", phoneNumber: "+292222222", language: "de"}
  ) {
    name
    phoneNumber
  }
}
```

Much like with users, once created, you can udpate more fields throught the mycompany mutation:

```graphql
mutation {
  updateMyMultiTenantCompany(data: {name: "New company Name"}) {
    name
  }
}
```


## Inviting Collegues

Once a user has been setup, it will be assigned as `is_multi_tenant_company_owner`. This can be transferred, should you wish but more importantly, this user can also invite other users via:

```graphql
mutation {
  inviteUser(
    data: {username: "invited@mail.com", language: "nl", firstName: "first name", lastName: "Last name"}
  ) {
    username
  }
}
```

Note that don't need to supply a password. OneSila will email the new user with an invitation link to create a password.

## Disabling / re-enabling users

The `is_multi_tenant_company_owner` account owner can also disable and re-enable other users.

```graphql
mutation {
  disableUser(
    data: {id:"GlobalIdforUser"}
  ) {
    username
  }
}
```

Once a user is disabled, they will no longer be able to log in.

In order to use this, you will need to find the relevant user ids.  There is no `users` query, instead you will need to find all users via the `myMultiTentantCompany` query:

```graphql
{
  myMultiTenantCompany {
    multitenantuserSet {
      id
      username
    }
  }
}
```


## Logging in a user

We have 2 ways of logging in.  The first is the classic, by way of username/email + password.
The second is via a login link.


### Classic username / password

```graphql
mutation{
  login(data:{username: "my@email.com", password: "my!291Pakd"}){
    username
  }
}
```


### Login Link

First request the login link, which will be sent to the user.

```graphql
mutation{
  requestLoginLink(data:{username: "my@email.com"}){
    username
  }
}
```

Once the user receives the link, you should take the ID from the link provided.
That link will be the ID with which you can call the actual login mutation.

```graphql
mutation{
  authenticateLoginLink(data:{id: "SomeGlobalID"}){
    username
  }
}
```

Remeber that the login-links expire.  This is controlled via the setting `MULTI_TENANT_LOGIN_LINK_EXPIRES_AFTER_MIN` in your settings file.

## Account Recovery

Account recovery is done through a magic login link.  This is the same mechanism as used to login a user via link, is conveniently sepparated to allow you to direct the user to setup a new password on the frontend.

Request the link via:

```graphql
mutation{
  recoverMe
}
```

Now you can authenticate using the same mutation as with loginLink.
After which you should be showing the user his/her password change page, instead of your usual login location.
