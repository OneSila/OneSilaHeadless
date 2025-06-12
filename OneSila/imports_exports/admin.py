from django.contrib import admin
from imports_exports.models import MappedImport
from django.utils.safestring import mark_safe
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

@admin.register(MappedImport)
class MappedImportAdmin(admin.ModelAdmin):
    readonly_fields = ['formatted_broken_records']
    exclude = ('broken_records',)

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