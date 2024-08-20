from core import models
from django.contrib.contenttypes.models import ContentType

class RemoteObjectMixin(models.Model):
    """
    Mixin that adds a remote_id field to track objects in remote systems,
    a sales_channel reference, and provides methods for logging related actions.
    Also includes a successfully_created field to track if the object was
    successfully created in the remote system.
    """

    remote_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID of the object in the remote system")
    sales_channel = models.ForeignKey('sales_channels.SalesChannel', on_delete=models.PROTECT, db_index=True)
    # if a mirror model was created but it fails next time we update it we will try update method because mirror model was created
    # to avoid that we have this field
    successfully_created = models.BooleanField(default=True, help_text="Indicates if the object was successfully created in the remote system.")

    # this should be overriden in the save we should make a qs on the logs to all the different identifier of the latest versions
    # they all need to be success for this to be true
    outdated = models.BooleanField(default=False, help_text="Indicates if the remote product is outdated due to an error.")

    class Meta:
        abstract = True

    def add_log(self, action, response, payload, *args, **kwargs):
        from .log import RemoteLog

        """
        Method to add a successful log entry.
        """
        self.create_log_entry(
            action=action,
            status=RemoteLog.STATUS_SUCCESS,
            response=response,
            payload=payload,
            *args, **kwargs
        )

    def add_error(self, action, response, payload, error_traceback, is_timeout=False, *args, **kwargs):
        from .log import RemoteLog
        """
        Method to add an error log entry.
        """
        status = RemoteLog.STATUS_TIMEOUT if is_timeout else RemoteLog.STATUS_FAILED
        self.create_log_entry(
            action=action,
            status=status,
            response=response,
            payload=payload,
            error_traceback=error_traceback,
            *args, **kwargs
        )

    def create_log_entry(self, action, status, response, payload, error_traceback=None, *args, **kwargs):
        from .log import RemoteLog
        """
        Method to create a log entry.
        """
        RemoteLog.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            content_object=self,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,  # Include the multi_tenant_company field
            action=action,
            status=status,
            response=response,
            payload=payload,
            error_traceback=error_traceback
        )
