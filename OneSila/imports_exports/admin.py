from django.contrib import admin
from imports_exports.models import Export, ImportBrokenRecord, ImportReport, MappedImport
from django.utils.safestring import mark_safe
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

@admin.register(MappedImport)
class MappedImportAdmin(admin.ModelAdmin):
    readonly_fields = ['formatted_broken_records']

    def formatted_broken_records(self, instance):
        if not instance.broken_records:
            return "—"

        response = json.dumps(instance.broken_records, sort_keys=True, indent=2, ensure_ascii=False)
        formatter = HtmlFormatter(style='colorful')
        highlighted = highlight(response, JsonLexer(), formatter)

        # Clean up and apply inline style
        style = f"<style>{formatter.get_style_defs()}</style><br>"
        return mark_safe(style + highlighted.replace('\\n', '<br/>'))

    formatted_broken_records.short_description = 'Broken Records'


@admin.register(Export)
class ExportAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "kind",
        "type",
        "status",
        "percentage",
        "is_periodic",
        "last_run_at",
        "created_at",
    )
    list_filter = ("kind", "type", "status", "is_periodic")
    search_fields = ("name", "feed_key", "kind", "type")
    readonly_fields = (
        "feed_key",
        "error_traceback",
        "file",
        "created_at",
        "updated_at",
        "feed_url",
        "formatted_parameters",
        "formatted_columns",
        # "formatted_raw_data",
    )
    exclude = ('raw_data',)
    actions = ("run_selected_exports", "regenerate_feed_keys")

    def feed_url(self, instance):
        if not instance.feed_key:
            return "—"
        return mark_safe(f'<a href="/direct/export/{instance.feed_key}/">/direct/export/{instance.feed_key}/</a>')

    feed_url.short_description = "Feed URL"

    def formatted_raw_data(self, instance):
        return _format_json(instance.raw_data)

    formatted_raw_data.short_description = "Raw Data"

    def formatted_parameters(self, instance):
        return _format_json(instance.parameters)

    formatted_parameters.short_description = "Parameters"

    def formatted_columns(self, instance):
        return _format_json(instance.columns)

    formatted_columns.short_description = "Columns"

    @admin.action(description="Run selected exports")
    def run_selected_exports(self, request, queryset):
        for export in queryset:
            export.status = Export.STATUS_PENDING
            export.error_traceback = ""
            export.save(update_fields=["status", "error_traceback"])

    @admin.action(description="Regenerate selected feed keys")
    def regenerate_feed_keys(self, request, queryset):
        for export in queryset.filter(type=Export.TYPE_JSON_FEED):
            export.feed_key = export._generate_feed_key()
            export.save(update_fields=["feed_key"])


@admin.register(ImportReport)
class ImportReportAdmin(admin.ModelAdmin):
    pass



@admin.register(ImportBrokenRecord)
class ImportBrokenRecordAdmin(admin.ModelAdmin):
    list_display = (
        'import_process',
        'import_status',
        'record_summary',
        'created_at',
    )
    list_filter = (
        'import_process__status',
        'import_process__skip_broken_records',
        'import_process__update_only',
        'import_process',
    )
    search_fields = (
        'import_process__name',
        'record__error',
        'record__message',
        'record__code',
        'record__step',
    )
    readonly_fields = ['formatted_record', 'created_at', 'updated_at']
    ordering = ('-created_at',)

    def import_status(self, obj):
        return obj.import_process.get_status_display()

    import_status.short_description = 'Import Status'

    def record_summary(self, obj):
        if not obj.record:
            return '—'
        for key in ('error', 'message', 'code', 'step'):
            value = obj.record.get(key)
            if value:
                return value
        return '—'

    record_summary.short_description = 'Summary'

    def formatted_record(self, instance):
        return _format_json(instance.record)

    formatted_record.short_description = 'Broken Record'


def _format_json(payload):
    if not payload:
        return "—"

    response = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)
    formatter = HtmlFormatter(style="colorful")
    highlighted = highlight(response, JsonLexer(), formatter)
    style = f"<style>{formatter.get_style_defs()}</style><br>"
    return mark_safe(style + highlighted.replace("\\n", "<br/>"))
