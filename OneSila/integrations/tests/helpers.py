from django.db import connection

from integrations.models import (
    PublicIntegrationType,
    PublicIntegrationTypeTranslation,
    PublicIssue,
    PublicIssueCategory,
    PublicIssueImage,
    PublicIssueRequest,
)


class PublicIntegrationTypeSchemaMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._created_public_integration_type_tables = []
        existing_tables = set(connection.introspection.table_names())

        with connection.schema_editor() as schema_editor:
            for model in (PublicIntegrationType, PublicIntegrationTypeTranslation):
                if model._meta.db_table in existing_tables:
                    continue

                schema_editor.create_model(model)
                cls._created_public_integration_type_tables.append(model)
                existing_tables.add(model._meta.db_table)

    @classmethod
    def tearDownClass(cls):
        created_tables = getattr(cls, "_created_public_integration_type_tables", [])
        with connection.schema_editor() as schema_editor:
            for model in reversed(created_tables):
                schema_editor.delete_model(model)

        super().tearDownClass()


class PublicIssueSchemaMixin(PublicIntegrationTypeSchemaMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._created_public_issue_tables = []
        existing_tables = set(connection.introspection.table_names())

        with connection.schema_editor() as schema_editor:
            for model in (PublicIssueRequest, PublicIssue, PublicIssueCategory, PublicIssueImage):
                if model._meta.db_table in existing_tables:
                    continue

                schema_editor.create_model(model)
                cls._created_public_issue_tables.append(model)
                existing_tables.add(model._meta.db_table)

    @classmethod
    def tearDownClass(cls):
        created_tables = getattr(cls, "_created_public_issue_tables", [])
        with connection.schema_editor() as schema_editor:
            for model in reversed(created_tables):
                schema_editor.delete_model(model)

        super().tearDownClass()
