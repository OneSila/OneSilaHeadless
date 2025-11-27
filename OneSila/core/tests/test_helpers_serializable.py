from core.helpers import ensure_serializable
from core.tests import TestCase


class EnsureSerializableTestCase(TestCase):
    def test_serializes_models_without_recursion(self):
        result = ensure_serializable(self.multi_tenant_company)
        self.assertIsInstance(result, str)

    def test_serializes_circular_references(self):
        class Node:
            def __init__(self):
                self.next = self

        node = Node()
        payload = {"node": node}

        result = ensure_serializable(payload)

        self.assertEqual(result["node"]["next"], "<circular Node>")
