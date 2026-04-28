from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from core import models


class Workflow(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    auto_add_on_product = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} <{self.code}>"

    @staticmethod
    def _normalise_code(*, value: str) -> str:
        normalised = slugify(value).replace("-", "_").upper()
        return normalised or "WORKFLOW"

    def _generate_unique_code(self):
        base_code = self._normalise_code(value=self.name)
        if not self.multi_tenant_company_id:
            return base_code

        queryset = self.__class__.objects.filter(
            multi_tenant_company_id=self.multi_tenant_company_id,
        ).exclude(id=self.id)

        code = base_code
        counter = 1
        while queryset.filter(code=code).exists():
            code = f"{base_code}_{counter}"
            counter += 1

        return code

    def save(self, *args, **kwargs):
        if self.name and not self.code:
            self.code = self._generate_unique_code()
        elif self.code:
            self.code = self._normalise_code(value=self.code)

        super().save(*args, **kwargs)

    class Meta:
        search_terms = ["name", "code", "description"]
        ordering = ("sort_order", "name", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["multi_tenant_company", "code"],
                name="unique_workflow_code_per_company",
                violation_error_message=_("This workflow code already exists for this company."),
            ),
        ]


class WorkflowState(models.Model):
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="states",
    )
    value = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.workflow.name}: {self.value}"

    @staticmethod
    def _normalise_code(*, value: str) -> str:
        normalised = slugify(value).replace("-", "_").upper()
        return normalised or "WORKFLOW_STATE"

    def _generate_unique_code(self):
        base_code = self._normalise_code(value=self.value)
        if not self.workflow_id:
            return base_code

        queryset = self.__class__.objects.filter(
            workflow_id=self.workflow_id,
        ).exclude(id=self.id)

        code = base_code
        counter = 1
        while queryset.filter(code=code).exists():
            code = f"{base_code}_{counter}"
            counter += 1

        return code

    def save(self, *args, **kwargs):
        if self.value and not self.code:
            self.code = self._generate_unique_code()
        elif self.code:
            self.code = self._normalise_code(value=self.code)

        super().save(*args, **kwargs)

    class Meta:
        search_terms = ["value", "code", "workflow__name", "workflow__code"]
        ordering = ("workflow_id", "sort_order", "-is_default", "value", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "code"],
                name="unique_workflow_state_code_per_workflow",
                violation_error_message=_("This workflow state code already exists for this workflow."),
            ),
            models.UniqueConstraint(
                fields=["workflow"],
                condition=Q(is_default=True),
                name="unique_default_workflow_state_per_workflow",
                violation_error_message=_("Only one default state is allowed per workflow."),
            ),
        ]


class WorkflowProductAssignment(models.Model):
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.PROTECT,
        related_name="product_assignments",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="workflow_assignments",
    )
    workflow_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.PROTECT,
        related_name="assignments",
    )

    def __str__(self):
        return f"{self.workflow.code} -> {self.product}"

    def clean(self):
        super().clean()

        if self.workflow_state_id and self.workflow_id != self.workflow_state.workflow_id:
            raise ValidationError(
                {
                    "workflow_state": _("The workflow state must belong to the selected workflow."),
                }
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        search_terms = [
            "workflow__name",
            "workflow__code",
            "workflow_state__value",
            "workflow_state__code",
            "product__sku",
        ]
        ordering = ("workflow__sort_order", "workflow_id", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "product"],
                name="unique_workflow_product_assignment",
                violation_error_message=_("This product is already assigned to the workflow."),
            ),
        ]
