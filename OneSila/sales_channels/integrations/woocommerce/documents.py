# Document model definitions for search indexing
# Example:
# from django_elasticsearch_dsl import Document, fields
# from django_elasticsearch_dsl.registries import registry
# from .models import SomeModel
#
# @registry.register_document
# class SomeModelDocument(Document):
#     class Index:
#         name = 'some_models'
#
#     class Django:
#         model = SomeModel
#         fields = ['field1', 'field2']
