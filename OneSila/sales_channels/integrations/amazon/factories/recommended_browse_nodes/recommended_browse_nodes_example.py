# @TODO: Example for Codex. Delete after we create the real factory + the periodic task (once a month)

import time
import gzip
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from sp_api.base.reportTypes import ReportType
from sp_api.base import ReportStatus

from sales_channels.integrations.amazon.models import AmazonBrowseNode


def sync_amazon_browse_nodes(marketplace_id, report_api):
    """
    Fully syncs all browse nodes from Amazon SP API GET_XML_BROWSE_TREE_DATA report.
    - Downloads fresh data from Amazon
    - Inserts new nodes
    - Removes old/stale nodes for that marketplace_id
    """
    # Step 1: Request report
    print("[STEP 1] Creating report...")
    response = report_api.create_report({
        "reportType": ReportType.GET_XML_BROWSE_TREE_DATA,
        "marketplaceIds": [marketplace_id],
    })
    report_id = response.report_id
    print(f"[INFO] Created report ID: {report_id}")

    # Step 2: Wait until done
    print("[STEP 2] Waiting for report to complete...")
    while True:
        report_info = report_api.get_report(report_id)
        status = report_info.processing_status

        if status == ReportStatus.DONE:
            print("[INFO] Report is done.")
            break
        elif status in (ReportStatus.CANCELLED, ReportStatus.FATAL):
            raise RuntimeError(f"[ERROR] Report failed: {status}")
        else:
            print(f"[WAITING] Still processing ({status}), sleeping 30s...")
            time.sleep(30)

    # Step 3: Download report document
    document_id = report_info.report_document_id
    doc_info = report_api.get_report_document(document_id)
    url = doc_info.url
    compression = doc_info.compression_algorithm
    print(f"[STEP 3] Downloading report document (compression: {compression})...")

    response = requests.get(url)
    content = response.content
    if compression == 'GZIP':
        content = gzip.decompress(content)
    xml_text = content.decode("utf-8")

    # Step 4: Parse all nodes
    print("[STEP 4] Parsing XML...")
    root = ET.fromstring(xml_text)
    nodes = root.findall(".//Node")

    print(f"[INFO] Found {len(nodes)} nodes in XML.")

    # Track all remote_ids to compare against DB later
    new_ids = set()
    new_objs = []

    for node_elem in tqdm(nodes, desc="Processing nodes"):
        def get_text(tag):
            el = node_elem.find(tag)
            return el.text.strip() if el is not None and el.text else None

        remote_id = get_text("browseNodeId")
        if not remote_id:
            continue

        name = get_text("browseNodeName")
        context_name = get_text("browseNodeStoreContextName")
        has_children = get_text("hasChildren") == "true"

        child_ids = []
        child_nodes = node_elem.find("childNodes")
        if child_nodes is not None:
            child_ids = [id_el.text.strip() for id_el in child_nodes.findall("id") if id_el.text]

        path_by_id = []
        bpid = get_text("browsePathById")
        if bpid:
            path_by_id = [s.strip() for s in bpid.split(",") if s.strip()]

        path_by_name = []
        bpname = get_text("browsePathByName")
        if bpname:
            path_by_name = [s.strip() for s in bpname.split(",") if s.strip()]

        ptd = node_elem.find("productTypeDefinitions")
        product_type_definitions = []
        if ptd is not None and ptd.text:
            product_type_definitions = [s.strip() for s in ptd.text.split(",") if s.strip()]

        is_root = len(path_by_id) == 2
        path_depth = len(path_by_id)

        new_ids.add(remote_id)

        new_objs.append(AmazonBrowseNode(
            remote_id=remote_id,
            marketplace_id=marketplace_id,
            name=name,
            context_name=context_name,
            has_children=has_children,
            is_root=is_root,
            child_node_ids=child_ids,
            browse_path_by_id=path_by_id,
            browse_path_by_name=path_by_name,
            product_type_definitions=product_type_definitions,
            path_depth=path_depth,
        ))

    print(f"[STEP 5] Saving {len(new_objs)} nodes to DB...")
    AmazonBrowseNode.objects.bulk_create(new_objs, ignore_conflicts=True)

    print("[STEP 6] Deleting stale nodes...")
    existing_ids = set(
        AmazonBrowseNode.objects.filter(marketplace_id=marketplace_id)
        .values_list("remote_id", flat=True)
    )

    stale_ids = existing_ids - new_ids
    if stale_ids:
        print(f"[INFO] Found {len(stale_ids)} stale nodes to delete...")
        AmazonBrowseNode.objects.filter(
            marketplace_id=marketplace_id, remote_id__in=stale_ids
        ).delete()
    else:
        print("[INFO] No stale nodes found.")

    print("[DONE] Amazon browse node sync complete.")


# from spapi import ReportsApi
#
# from sales_channels.integrations.amazon.factories.sales_channels.full_schema import AmazonProductTypeRuleFactory
# from sales_channels.integrations.amazon.models import AmazonSalesChannel
# sales_channel = AmazonSalesChannel.objects.first()
#
#
# fac = AmazonProductTypeRuleFactory(
#     product_type_code='CABINET',
#     sales_channel=sales_channel,
# )
# api = ReportsApi(fac._get_client())
#
# sync_amazon_browse_nodes("A1F83G8C2ARO7P", api)
