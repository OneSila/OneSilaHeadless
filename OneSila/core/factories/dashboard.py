from __future__ import annotations

from typing import Dict

from django.db import transaction

from get_absolute_url.helpers import generate_absolute_url

from core.defaults import DASHBOARD_SECTION_DEFINITIONS
from core.models.multi_tenant import DashboardSection, DashboardCard, MultiTenantUser


class DashboardDefaultsFactory:
    def __init__(self, *, user: MultiTenantUser):
        self.user = user
        self.company = user.multi_tenant_company
        self.base_url = generate_absolute_url(trailing_slash=False)

    def _update_model_fields(self, *, instance, data: Dict):
        updated_fields = []
        for field_name, value in data.items():
            if getattr(instance, field_name) != value:
                setattr(instance, field_name, value)
                updated_fields.append(field_name)

        if updated_fields:
            instance.last_update_by_multi_tenant_user = self.user
            updated_fields.append("last_update_by_multi_tenant_user")
            instance.save(update_fields=updated_fields)

    def _ensure_sections(self) -> Dict[str, DashboardSection]:
        sections: Dict[str, DashboardSection] = {}

        for section_def in DASHBOARD_SECTION_DEFINITIONS:
            defaults = {
                "description": section_def["description"],
                "sort_order": section_def["sort_order"],
            }
            section, created = DashboardSection.objects.get_or_create(
                user=self.user,
                multi_tenant_company=self.company,
                title=section_def["title"],
                defaults=defaults,
            )

            if not created:
                updates = {
                    "description": section_def["description"],
                    "sort_order": section_def["sort_order"],
                }
                if section.multi_tenant_company_id != self.company_id:
                    updates["multi_tenant_company"] = self.company
                self._update_model_fields(instance=section, data=updates)

            sections[section_def["identifier"]] = section

        return sections

    @property
    def company_id(self):
        return getattr(self.company, "id", None)

    def _ensure_cards(self, *, section: DashboardSection, section_def: dict):
        cards = section_def.get("cards", [])
        if not cards:
            return

        for order, card_def in enumerate(cards, start=1):
            variables = card_def.get("variables", {}).copy()
            error_code = variables.get("errorCode")
            url_path = card_def.get("url_path")
            full_url = f"{self.base_url}{url_path}" if url_path else None
            lookup_kwargs = {
                "multi_tenant_company": self.company,
                "user": self.user,
                "section": section,
                "query_key": card_def["query_key"],
                "url": full_url,
            }
            if error_code is not None:
                lookup_kwargs["variables__errorCode"] = error_code
            else:
                lookup_kwargs["variables"] = variables

            defaults = {
                "title": card_def["title"],
                "description": card_def["description"],
                "color": card_def["color"],
                "query": card_def["query"],
                "variables": variables,
                "sort_order": card_def.get("sort_order", order),
                "url": full_url,
            }
            card, created = DashboardCard.objects.get_or_create(
                defaults=defaults,
                **lookup_kwargs,
            )

            if not created:
                updates = {
                    "title": card_def["title"],
                    "description": card_def["description"],
                    "color": card_def["color"],
                    "query": card_def["query"],
                    "variables": variables,
                    "sort_order": card_def.get("sort_order", order),
                    "url": full_url,
                }
                if card.multi_tenant_company_id != self.company_id:
                    updates["multi_tenant_company"] = self.company
                self._update_model_fields(instance=card, data=updates)

    @transaction.atomic
    def work(self):
        if self.company is None:
            return

        sections = self._ensure_sections()
        for section_def in DASHBOARD_SECTION_DEFINITIONS:
            section = sections.get(section_def["identifier"])
            if section is None:
                continue
            self._ensure_cards(section=section, section_def=section_def)
