from integrations.factories.mixins import IntegrationInstanceCreateFactory

class AccountingRemoteInstanceCreateFactory(IntegrationInstanceCreateFactory):
    integration_key = 'remote_account'

    def __init__(self, remote_account, local_instance, api=None):
        super().__init__(integration=remote_account, local_instance=local_instance, api=api)