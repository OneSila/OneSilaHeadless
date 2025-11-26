from integrations.models import IntegrationLog


class RemoteLog(IntegrationLog):
    pass

    class Meta:
        verbose_name = 'Remote Log'
        verbose_name_plural = 'Remote Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Log for {self.content_object} - Action: {self.action}, Status: {self.status}"
