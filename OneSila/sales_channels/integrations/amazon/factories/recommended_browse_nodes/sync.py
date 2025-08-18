import gzip
import time
import xml.etree.ElementTree as ET
from typing import Iterable

import requests
from sp_api.base import ReportStatus
from sp_api.base.reportTypes import ReportType
from spapi import ReportsApi

from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import AmazonBrowseNode, AmazonSalesChannelView


class AmazonBrowseNodeSyncFactory(GetAmazonAPIMixin):
    """Sync all Amazon browse nodes for a given marketplace view."""

    def __init__(self, view: AmazonSalesChannelView):
        self.view = view
        self.sales_channel = view.sales_channel
        self.marketplace_id = view.remote_id
        self.api = ReportsApi(self._get_client())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _wait_for_report(self, report_id: str):
        while True:
            report_info = self.api.get_report(report_id)
            status = report_info.processing_status
            if status == ReportStatus.DONE:
                return report_info
            if status in (ReportStatus.CANCELLED, ReportStatus.FATAL):
                raise RuntimeError(f"Report failed: {status}")
            time.sleep(30)

    def _download_document(self, report_document_id: str) -> str:
        doc_info = self.api.get_report_document(report_document_id)
        content = requests.get(doc_info.url).content
        if doc_info.compression_algorithm == "GZIP":
            content = gzip.decompress(content)
        return content.decode("utf-8")

    def _parse_nodes(self, xml_text: str) -> Iterable[AmazonBrowseNode]:
        root = ET.fromstring(xml_text)
        nodes = root.findall(".//Node")
        for node_elem in nodes:
            remote_id = node_elem.findtext("browseNodeId")
            if not remote_id:
                continue
            name = node_elem.findtext("browseNodeName")
            context_name = node_elem.findtext("browseNodeStoreContextName")
            has_children = node_elem.findtext("hasChildren") == "true"
            child_ids = [el.text.strip() for el in node_elem.findall("childNodes/id") if el.text]
            path_by_id = [s.strip() for s in (node_elem.findtext("browsePathById") or "").split(",") if s.strip()]
            path_by_name = [s.strip() for s in (node_elem.findtext("browsePathByName") or "").split(",") if s.strip()]
            ptd_text = node_elem.findtext("productTypeDefinitions") or ""
            product_type_definitions = [s.strip() for s in ptd_text.split(",") if s.strip()]
            is_root = len(path_by_id) == 2
            path_depth = len(path_by_id)
            yield AmazonBrowseNode(
                remote_id=remote_id,
                marketplace_id=self.marketplace_id,
                name=name,
                context_name=context_name,
                has_children=has_children,
                is_root=is_root,
                child_node_ids=child_ids,
                browse_path_by_id=path_by_id,
                browse_path_by_name=path_by_name,
                product_type_definitions=product_type_definitions,
                path_depth=path_depth,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self):
        response = self.api.create_report(
            {
                "reportType": ReportType.GET_XML_BROWSE_TREE_DATA,
                "marketplaceIds": [self.marketplace_id],
            }
        )
        report_info = self._wait_for_report(response.report_id)
        xml_text = self._download_document(report_info.report_document_id)
        new_objs = list(self._parse_nodes(xml_text))
        new_ids = {obj.remote_id for obj in new_objs}
        AmazonBrowseNode.objects.bulk_create(new_objs, ignore_conflicts=True)
        existing_ids = set(
            AmazonBrowseNode.objects.filter(marketplace_id=self.marketplace_id).values_list("remote_id", flat=True)
        )
        stale_ids = existing_ids - new_ids
        if stale_ids:
            AmazonBrowseNode.objects.filter(
                marketplace_id=self.marketplace_id, remote_id__in=stale_ids
            ).delete()
