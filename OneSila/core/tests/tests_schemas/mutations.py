
REGISTER_USER_MUTATION = """
  mutation registerUser($username: String!, $password: String!, $language: String!) {
    registerUser(data: {username: $username, password: $password, language: $language}) {
      username
      password
      invitationAccepted
      isMultiTenantCompanyOwner
    }
  }
"""


LOGIN_MUTATION = """
  mutation login($username: String!, $password: String!) {
    login(username: $username, password: $password){
      username
    }
  }
"""


LOGOUT_MUTATION = """
  mutation logout {
      logout
  }
"""


ME_QUERY = """
  query me {
    me {
      username
      password
      language
      multiTenantCompany{
        id
      }
      avatarResizedFullUrl
      avatar {
        name
        path
        url
        width
      }
      avatarResized {
        name
        path
        url
        size
      }
    }
  }
"""
