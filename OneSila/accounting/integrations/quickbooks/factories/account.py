from intuitlib.client import AuthClient
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class QuickbooksAccountAuthorizationFactory:
    """
    Factory for handling the initial OAuth2 setup for QuickBooks, exchanging the authorization code
    and realm ID for access and refresh tokens.
    """
    def __init__(self, remote_account):
        self.remote_account = remote_account

    def get_auth_client(self):
        """
        Instantiate the AuthClient for OAuth2.
        """
        return AuthClient(
            client_id=self.remote_account.client_id,
            client_secret=self.remote_account.client_secret,
            environment=self.remote_account.environment,
            redirect_uri=self.remote_account.redirect_uri
        )

    def run(self):
        """
        Exchange the authorization code for access and refresh tokens.
        """
        authorization_code = self.remote_account.authorization_code
        realm_id = self.remote_account.realm_id

        if not authorization_code or not realm_id:
            raise ValueError("Authorization code and Realm ID are required.")

        try:
            auth_client = self.get_auth_client()
            token_response = auth_client.get_bearer_token(authorization_code, realm_id=realm_id)


            access_token_expiration = timezone.now() + timedelta(minutes=60)

            # Store tokens in the database
            self.remote_account.access_token = auth_client.access_token
            self.remote_account.refresh_token = auth_client.refresh_token
            self.remote_account.token_expiration = access_token_expiration
            self.remote_account.save()

            logger.info(f"Successfully exchanged authorization code for tokens.")
        except Exception as e:
            logger.error(f"Failed to exchange authorization code: {e}")
            raise
