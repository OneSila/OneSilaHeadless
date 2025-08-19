from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.tests import TestCase
from sales_channels.integrations.amazon.models import AmazonBrowseNode, AmazonSalesChannel, AmazonSalesChannelView
from sales_channels.integrations.amazon.factories.recommended_browse_nodes import AmazonBrowseNodeSyncFactory


class AmazonBrowseNodeSyncFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            api_region_code="EU_UK",
            remote_id="GB",
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    def test_sets_parent_node(self, _):
        xml = """
        <Nodes>
            <Node>
                <browseNodeId>1</browseNodeId>
                <browseNodeName>Root</browseNodeName>
                <hasChildren>true</hasChildren>
                <childNodes><id>2</id></childNodes>
                <browsePathById>0,1</browsePathById>
            </Node>
            <Node>
                <browseNodeId>2</browseNodeId>
                <browseNodeName>Child</browseNodeName>
                <hasChildren>false</hasChildren>
                <childNodes />
                <browsePathById>0,1,2</browsePathById>
            </Node>
        </Nodes>
        """

        fac = AmazonBrowseNodeSyncFactory(self.view)
        fac.api.create_report = Mock(return_value=SimpleNamespace(report_id="rid"))
        fac._wait_for_report = Mock(return_value=SimpleNamespace(report_document_id="doc"))
        fac._download_document = Mock(return_value=xml)

        fac.run()

        root = AmazonBrowseNode.objects.get(remote_id="1")
        child = AmazonBrowseNode.objects.get(remote_id="2")
        self.assertEqual(child.parent_node, root)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    def test_marks_root_when_parent_missing(self, _):
        xml = """
        <Nodes>
            <Node>
                <browseNodeId>573406</browseNodeId>
                <browseNodeName>DVD &amp; Blu-ray</browseNodeName>
                <hasChildren>false</hasChildren>
                <childNodes />
                <browsePathById>283920,283926,573406</browsePathById>
                <browsePathByName>DVD &amp; Blu-ray</browsePathByName>
            </Node>
        </Nodes>
        """

        fac = AmazonBrowseNodeSyncFactory(self.view)
        fac.api.create_report = Mock(return_value=SimpleNamespace(report_id="rid"))
        fac._wait_for_report = Mock(return_value=SimpleNamespace(report_document_id="doc"))
        fac._download_document = Mock(return_value=xml)

        fac.run()

        node = AmazonBrowseNode.objects.get(remote_id="573406")
        self.assertTrue(node.is_root)
        self.assertIsNone(node.parent_node)
