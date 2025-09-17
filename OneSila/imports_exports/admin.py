from django.contrib import admin
from imports_exports.models import MappedImport, ImportReport, ImportBrokenRecord
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
        if not instance.record:
            return "—"

        response = json.dumps(instance.record, sort_keys=True, indent=2, ensure_ascii=False)
        formatter = HtmlFormatter(style='colorful')
        highlighted = highlight(response, JsonLexer(), formatter)

        style = f"<style>{formatter.get_style_defs()}</style><br>"
        return mark_safe(style + highlighted.replace('\\n', '<br/>'))

    formatted_record.short_description = 'Broken Record'
