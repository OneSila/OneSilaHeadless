from collections import Counter, defaultdict
import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tqdm import tqdm

from core.locales import LEGACY_LANGUAGE_CONVERTOR
from core.models import MultiTenantCompany, MultiTenantUser
from imports_exports.models import TypedImport
from integrations.models import PublicIntegrationTypeTranslation
from llm.models import BrandCustomPrompt
from media.models import Media
from products.models import ProductTranslation
from properties.models import (
    ProductPropertyTextTranslation,
    PropertySelectValueTranslation,
    PropertyTranslation,
)
from sales_channels.models.products import RemoteProductContent
from sales_channels.models.sales_channels import RemoteLanguage, SalesChannelContentTemplate


class Command(BaseCommand):
    help = "Convert legacy language codes to locale-based language codes."

    SECTION_ORDER = (
        "companies",
        "users",
        "imports",
        "integrations",
        "llm_prompts",
        "media",
        "sales_channel_languages",
        "property_translations",
        "product_translations",
        "remote_product_content",
    )

    def add_arguments(self, parser):
        parser.add_argument("--mtc-id", type=int, default=None)
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--companies", action="store_true")
        parser.add_argument("--users", action="store_true")
        parser.add_argument("--product-translations", action="store_true")
        parser.add_argument("--property-translations", action="store_true")
        parser.add_argument("--remote-product-content", action="store_true")
        parser.add_argument("--sales-channel-languages", action="store_true")
        parser.add_argument("--imports", action="store_true")
        parser.add_argument("--media", action="store_true")
        parser.add_argument("--integrations", action="store_true")
        parser.add_argument("--llm-prompts", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.limit = options["limit"]
        self.mtc_id = options["mtc_id"]
        self.unknown_values = defaultdict(Counter)
        self.conflicts = defaultdict(Counter)

        sections = self._get_selected_sections(options=options)
        if not sections:
            raise CommandError("Select at least one section or use --all.")

        self.stdout.write(
            self.style.NOTICE(
                f"Starting language conversion. dry_run={self.dry_run} mtc_id={self.mtc_id or 'all'}"
            )
        )

        for section in sections:
            with transaction.atomic():
                getattr(self, f"_handle_{section}")()
                if self.dry_run:
                    transaction.set_rollback(True)

        self._write_summary()

    def _get_selected_sections(self, *, options) -> list[str]:
        if options["all"]:
            return list(self.SECTION_ORDER)

        selected = []
        if options["companies"]:
            selected.append("companies")
        if options["users"]:
            selected.append("users")
        if options["imports"]:
            selected.append("imports")
        if options["integrations"]:
            selected.append("integrations")
        if options["llm_prompts"]:
            selected.append("llm_prompts")
        if options["media"]:
            selected.append("media")
        if options["sales_channel_languages"]:
            selected.append("sales_channel_languages")
        if options["property_translations"]:
            selected.append("property_translations")
        if options["product_translations"]:
            selected.append("product_translations")
        if options["remote_product_content"]:
            selected.append("remote_product_content")
        return selected

    def _handle_companies(self):
        queryset = MultiTenantCompany.objects.all().order_by("id")
        queryset = self._apply_limit(queryset=queryset)
        self._write_section_header(name="companies", total=queryset.count())

        processed = changed = skipped = 0
        progress = self._build_progress_bar(name="companies", total=queryset.count())
        for company in queryset.iterator():
            processed += 1
            changed_language, new_language = self._convert_scalar_language(
                section="companies.language",
                value=company.language,
            )
            changed_languages, new_languages = self._convert_language_list(
                section="companies.languages",
                values=company.languages or [],
            )

            if changed_language or changed_languages:
                changed += 1
                if not self.dry_run:
                    company.language = new_language
                    company.languages = new_languages
                    company.save(update_fields=["language", "languages"])
            else:
                skipped += 1

            self._advance_progress(progress=progress, changed=changed, skipped=skipped)

        progress.close()

        self._write_section_footer(name="companies", processed=processed, changed=changed, skipped=skipped)

    def _handle_users(self):
        self._run_simple_language_section(
            name="users",
            queryset=MultiTenantUser.objects.all().order_by("id"),
            field_name="language",
            mtc_lookup="multi_tenant_company_id",
        )

    def _handle_imports(self):
        self._run_simple_language_section(
            name="imports",
            queryset=TypedImport.objects.all().order_by("id"),
            field_name="language",
            mtc_lookup="multi_tenant_company_id",
        )

    def _handle_integrations(self):
        self._run_simple_language_section(
            name="integrations",
            queryset=PublicIntegrationTypeTranslation.objects.all().order_by("id"),
            field_name="language",
            mtc_lookup=None,
        )

    def _handle_llm_prompts(self):
        self._run_simple_language_section(
            name="llm_prompts",
            queryset=BrandCustomPrompt.objects.all().order_by("id"),
            field_name="language",
            mtc_lookup="brand_value__property__multi_tenant_company_id",
        )

    def _handle_media(self):
        self._run_simple_language_section(
            name="media",
            queryset=Media.objects.exclude(document_language__isnull=True).exclude(document_language="").order_by("id"),
            field_name="document_language",
            mtc_lookup="multi_tenant_company_id",
        )

    def _handle_sales_channel_languages(self):
        self._run_simple_language_section(
            name="sales_channel_templates",
            queryset=SalesChannelContentTemplate.objects.all().order_by("id"),
            field_name="language",
            mtc_lookup="sales_channel__multi_tenant_company_id",
        )
        self._run_simple_language_section(
            name="remote_languages",
            queryset=RemoteLanguage.objects.exclude(local_instance__isnull=True).exclude(local_instance="").order_by("id"),
            field_name="local_instance",
            mtc_lookup="sales_channel__multi_tenant_company_id",
            require_real_instance=True,
        )

    def _handle_property_translations(self):
        self._run_simple_language_section(
            name="property_translations",
            queryset=PropertyTranslation.objects.all().order_by("id"),
            field_name="language",
            mtc_lookup="multi_tenant_company_id",
        )
        self._run_simple_language_section(
            name="property_select_value_translations",
            queryset=PropertySelectValueTranslation.objects.all().order_by("id"),
            field_name="language",
            mtc_lookup="multi_tenant_company_id",
        )

    def _handle_product_translations(self):
        self._run_simple_language_section(
            name="product_property_text_translations",
            queryset=ProductPropertyTextTranslation.objects.all().order_by("id"),
            field_name="language",
            mtc_lookup="multi_tenant_company_id",
        )
        self._run_simple_language_section(
            name="product_translations",
            queryset=ProductTranslation.objects.all().order_by("id"),
            field_name="language",
            mtc_lookup="multi_tenant_company_id",
        )

    def _handle_remote_product_content(self):
        queryset = RemoteProductContent.objects.all().order_by("id")
        queryset = self._filter_queryset(queryset=queryset, mtc_lookup="remote_product__sales_channel__multi_tenant_company_id")
        queryset = self._apply_limit(queryset=queryset)
        self._write_section_header(name="remote_product_content", total=queryset.count())

        processed = changed = skipped = 0
        progress = self._build_progress_bar(name="remote_product_content", total=queryset.count())
        for remote_content in queryset.iterator():
            processed += 1
            real_instance = remote_content.get_real_instance()
            did_change, new_data = self._convert_language_dict(
                section="remote_product_content",
                data=real_instance.content_data or {},
            )
            if did_change:
                changed += 1
                if not self.dry_run:
                    real_instance.content_data = new_data
                    real_instance.save()
            else:
                skipped += 1

            self._advance_progress(progress=progress, changed=changed, skipped=skipped)

        progress.close()

        self._write_section_footer(
            name="remote_product_content",
            processed=processed,
            changed=changed,
            skipped=skipped,
        )

    def _run_simple_language_section(self, *, name, queryset, field_name, mtc_lookup, require_real_instance=False):
        queryset = self._filter_queryset(queryset=queryset, mtc_lookup=mtc_lookup)
        queryset = self._apply_limit(queryset=queryset)
        self._write_section_header(name=name, total=queryset.count())

        processed = changed = skipped = 0
        progress = self._build_progress_bar(name=name, total=queryset.count())
        for instance in queryset.iterator():
            processed += 1
            real_instance = instance.get_real_instance() if require_real_instance else instance
            current_value = getattr(real_instance, field_name)
            did_change, new_value = self._convert_scalar_language(section=name, value=current_value)

            if did_change:
                changed += 1
                if not self.dry_run:
                    real_instance.__class__.objects.filter(pk=real_instance.pk).update(**{field_name: new_value})
            else:
                skipped += 1

            self._advance_progress(progress=progress, changed=changed, skipped=skipped)

        progress.close()

        self._write_section_footer(name=name, processed=processed, changed=changed, skipped=skipped)

    def _convert_scalar_language(self, *, section, value):
        normalized = str(value or "").strip()
        if not normalized:
            return False, value

        lowered = normalized.lower()
        converted = LEGACY_LANGUAGE_CONVERTOR.get(lowered)
        if converted:
            return converted != normalized, converted

        if lowered in LEGACY_LANGUAGE_CONVERTOR.values():
            return False, normalized

        self.unknown_values[section][normalized] += 1
        return False, normalized

    def _convert_language_list(self, *, section, values):
        if not values:
            return False, values

        new_values = []
        seen = set()
        changed = False

        for value in values:
            did_change, new_value = self._convert_scalar_language(section=section, value=value)
            if did_change:
                changed = True

            if new_value in seen:
                changed = True
                continue

            seen.add(new_value)
            new_values.append(new_value)

        return changed or list(values) != new_values, new_values

    def _convert_language_dict(self, *, section, data):
        if not data:
            return False, data

        new_data = {}
        changed = False

        for key, value in data.items():
            did_change, new_key = self._convert_scalar_language(section=section, value=key)
            if did_change:
                changed = True

            if new_key in new_data and new_data[new_key] != value:
                self.conflicts[section][new_key] += 1
                continue

            if new_key != key:
                changed = True

            new_data[new_key] = value

        return changed or data != new_data, new_data

    def _filter_queryset(self, *, queryset, mtc_lookup):
        if self.mtc_id is not None and mtc_lookup:
            return queryset.filter(**{mtc_lookup: self.mtc_id})
        return queryset

    def _apply_limit(self, *, queryset):
        if self.limit:
            return queryset[:self.limit]
        return queryset

    def _write_section_header(self, *, name, total):
        self.stdout.write(self.style.NOTICE(f"[{name}] starting total={total}"))

    def _write_section_footer(self, *, name, processed, changed, skipped):
        self.stdout.write(
            self.style.SUCCESS(
                f"[{name}] done processed={processed} changed={changed} skipped={skipped}"
            )
        )

    def _build_progress_bar(self, *, name, total):
        return tqdm(
            total=total,
            desc=name,
            unit="row",
            file=sys.stdout,
            mininterval=0.5,
            dynamic_ncols=True,
            leave=True,
        )

    def _advance_progress(self, *, progress, changed, skipped):
        progress.update(1)
        if progress.n == 1 or progress.n % 1000 == 0 or progress.n == progress.total:
            progress.set_postfix(changed=changed, skipped=skipped, refresh=False)

    def _write_summary(self):
        if self.unknown_values:
            self.stdout.write(self.style.WARNING("Unknown values encountered:"))
            for section, values in self.unknown_values.items():
                summary = ", ".join(f"{value} x{count}" for value, count in values.most_common())
                self.stdout.write(f" - {section}: {summary}")

        if self.conflicts:
            self.stdout.write(self.style.WARNING("Key conflicts encountered:"))
            for section, values in self.conflicts.items():
                summary = ", ".join(f"{value} x{count}" for value, count in values.most_common())
                self.stdout.write(f" - {section}: {summary}")

        self.stdout.write(self.style.SUCCESS("Language conversion finished."))
