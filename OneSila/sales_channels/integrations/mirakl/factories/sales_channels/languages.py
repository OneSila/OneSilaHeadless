from django.conf import settings

from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import MiraklRemoteLanguage


def _map_local_language(*, code: str) -> str:
    normalized = str(code or "").strip()
    languages = {entry[0] for entry in settings.LANGUAGES}
    if normalized in languages:
        return normalized
    lowered = normalized.lower()
    if lowered in languages:
        return lowered
    base = lowered.split("_")[0].split("-")[0]
    return base if base in languages else settings.LANGUAGE_CODE


class MiraklRemoteLanguagePullFactory(GetMiraklAPIMixin, PullRemoteInstanceMixin):
    """Pull Mirakl locales/languages."""

    remote_model_class = MiraklRemoteLanguage
    field_mapping = {
        "remote_code": "code",
        "label": "label",
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ["remote_code"]

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        response = self.mirakl_get(path="/api/locales")
        locales = response.get("locales") or []
        self.remote_instances = [locale for locale in locales if isinstance(locale, dict)]

    def create_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        remote_instance_mirror.remote_code = remote_data.get("code", "")
        remote_instance_mirror.label = remote_data.get("label", "")
        remote_instance_mirror.local_instance = _map_local_language(code=remote_instance_mirror.remote_code)
        remote_instance_mirror.is_default = bool(remote_data.get("platform_default"))
        remote_instance_mirror.sales_channel = self.sales_channel
        remote_instance_mirror.multi_tenant_company = self.sales_channel.multi_tenant_company
        remote_instance_mirror.save()

    def add_fields_to_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        remote_instance_mirror.label = remote_data.get("label", "")
        remote_instance_mirror.local_instance = _map_local_language(code=remote_data.get("code", ""))
        remote_instance_mirror.is_default = bool(remote_data.get("platform_default"))
        remote_instance_mirror.save(update_fields=["label", "local_instance", "is_default"])
