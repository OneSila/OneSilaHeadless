import abc
import logging
from traceback import format_exc

from core.helpers import ensure_serializable
from core.locales import LANGUAGE_MAX_LENGTH
from sales_channels.models import SalesChannel

logger = logging.getLogger(__name__)


class AbstractExportFactory(abc.ABC):
    kind = None
    default_columns = ()
    supported_columns = ()
    iterator_chunk_size = 200
    progress_log_step = 100

    def __init__(self, *, export_process, columns=None, parameters=None, language=None):
        self.export_process = export_process
        self.multi_tenant_company = export_process.multi_tenant_company
        if language is not None:
            self.language = language
        else:
            self.language = export_process.language
        self.parameters = parameters if parameters is not None else (export_process.parameters or {})
        if columns is None:
            self.columns = list(export_process.columns or self.supported_columns)
        else:
            self.columns = list(columns)
        self._resolved_sales_channel = None
        self._sales_channel_resolved = False
        self._progress_step = 0
        self._tracked_total_records = None
        self._last_logged_processed = 0

        self.validate()

    def validate(self):
        unsupported_columns = sorted(set(self.columns) - set(self.supported_columns))
        if unsupported_columns:
            raise ValueError(
                f"Unsupported columns for {self.kind}: {', '.join(unsupported_columns)}"
            )

        if self.language and len(self.language) > LANGUAGE_MAX_LENGTH:
            raise ValueError("Invalid export language.")

    def include_column(self, *, key):
        return not self.columns or key in self.columns

    def get_parameter(self, *, key, default=None):
        return self.parameters.get(key, default)

    def get_nested_parameter(self, *, key, nested_key, default=None):
        nested = self.parameters.get(key)
        if not isinstance(nested, dict):
            return default
        return nested.get(nested_key, default)

    def normalize_ids(self, *, value):
        if value in (None, ""):
            return []

        if isinstance(value, (list, tuple, set)):
            raw_values = value
        else:
            raw_values = [value]

        ids = []
        for raw_value in raw_values:
            if raw_value in (None, ""):
                continue
            ids.append(int(raw_value))
        return ids

    def build_payload(self):
        data = self.get_payload()
        return ensure_serializable(data)

    @abc.abstractmethod
    def get_payload(self):
        raise NotImplementedError

    def get_total_records(self, *, payload):
        if self._tracked_total_records is not None:
            return self._tracked_total_records

        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict):
            return 1
        return 0

    def track_queryset(self, *, queryset):
        total_records = queryset.count()
        self._tracked_total_records = total_records
        self.export_process.total_records = total_records
        self.export_process.save(update_fields=["total_records"])
        logger.info(
            "Export %s (%s) will build raw_data for %s records.",
            self.export_process.id,
            self.kind,
            total_records,
        )
        return total_records

    def get_queryset_total_records(self):
        queryset = self.get_queryset()
        return queryset.count()

    def validate_periodic_record_limit(self):
        if not self.export_process.is_periodic:
            return

        total_records = self.get_queryset_total_records()
        if total_records > self.export_process.PERIODIC_MAX_TOTAL_RECORDS:
            raise ValueError(
                f"Periodic exports are limited to {self.export_process.PERIODIC_MAX_TOTAL_RECORDS} records. "
                f"This export would process {total_records} records."
            )

    def iterate_queryset(self, *, queryset):
        return queryset.iterator(chunk_size=self.iterator_chunk_size)

    def update_progress(self, *, processed, total_records):
        if total_records <= 0:
            return

        self.log_progress(processed=processed, total_records=total_records)

        percentage = int((processed * 100) / total_records)
        percentage = min((percentage // 10) * 10, 90)

        if percentage <= self._progress_step:
            return

        self._progress_step = percentage
        self.export_process.percentage = percentage
        self.export_process.save(update_fields=["percentage"])

    def log_progress(self, *, processed, total_records):
        if processed != total_records and processed - self._last_logged_processed < self.progress_log_step:
            return

        self._last_logged_processed = processed
        logger.info(
            "Export %s (%s) built raw_data for %s/%s records.",
            self.export_process.id,
            self.kind,
            processed,
            total_records,
        )

    def resolve_sales_channel(self):
        if self._sales_channel_resolved:
            return self._resolved_sales_channel

        sales_channel = self.get_parameter(key="sales_channel")
        if sales_channel in [None, ""]:
            self._sales_channel_resolved = True
            self._resolved_sales_channel = None
            return self._resolved_sales_channel

        if isinstance(sales_channel, SalesChannel):
            self._sales_channel_resolved = True
            self._resolved_sales_channel = sales_channel
            return self._resolved_sales_channel

        resolved_channel = SalesChannel.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            id=sales_channel,
        ).first()
        if resolved_channel is None:
            raise ValueError(f"Sales channel {sales_channel} does not exist for this company.")
        self._sales_channel_resolved = True
        self._resolved_sales_channel = resolved_channel
        return self._resolved_sales_channel

    def assert_language_supported(self):
        if not self.language:
            return

        company_languages = getattr(self.multi_tenant_company, "languages", []) or []
        company_default = getattr(self.multi_tenant_company, "language", None)
        allowed_languages = set(company_languages)
        if company_default:
            allowed_languages.add(company_default)

        if allowed_languages and self.language not in allowed_languages:
            raise ValueError(f"Language {self.language} is not enabled for this company.")


class ExportRunner:
    def __init__(self, *, export_process):
        self.export_process = export_process

    def run(self):
        from imports_exports.factories.exports.registry import get_export_factory

        export_process = self.export_process
        logger.info(
            "Starting export %s (%s, %s).",
            export_process.id,
            export_process.kind,
            export_process.type,
        )
        export_process.status = export_process.STATUS_PROCESSING
        export_process.percentage = 0
        export_process.error_traceback = ""
        export_process.raw_data = []
        export_process.save(update_fields=["status", "percentage", "error_traceback", "raw_data"])

        try:
            factory_class = get_export_factory(kind=export_process.kind)
            factory = factory_class(export_process=export_process)
            factory.validate_periodic_record_limit()
            raw_data = factory.build_payload()

            export_process.total_records = factory.get_total_records(payload=raw_data)
            export_process.percentage = max(export_process.percentage, 90)
            export_process.raw_data = []
            export_process.save(update_fields=["raw_data", "total_records", "percentage"])

            export_process.generate_file(raw_data=raw_data)

            update_fields = ["status", "percentage", "raw_data", "total_records", "error_traceback"]
            if export_process.file:
                update_fields.append("file")

            export_process.status = export_process.STATUS_SUCCESS
            export_process.percentage = 100
            export_process.error_traceback = ""
            export_process.save(update_fields=update_fields)
            logger.info(
                "Export %s (%s) completed successfully with %s records.",
                export_process.id,
                export_process.kind,
                export_process.total_records,
            )

        except Exception:
            export_process.status = export_process.STATUS_FAILED
            export_process.percentage = 100
            export_process.error_traceback = format_exc()
            export_process.raw_data = []

            update_fields = ["status", "percentage", "error_traceback", "raw_data", "total_records"]
            if export_process.file:
                update_fields.append("file")
            export_process.save(update_fields=update_fields)
            logger.exception(
                "Export %s (%s) failed while building raw_data or materializing the file.",
                export_process.id,
                export_process.kind,
            )
