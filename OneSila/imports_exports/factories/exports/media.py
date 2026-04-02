from media.models import Media, MediaProductThrough

from .helpers import build_product_stub, to_bool
from .mixins import AbstractExportFactory


class BaseMediaExportFactory(AbstractExportFactory):
    media_type = None
    supported_columns = (
        "image_url",
        "video_url",
        "document_url",
        "type",
        "title",
        "description",
        "product_data",
        "product_sku",
        "sort_order",
        "is_main_image",
        "document_type",
        "document_language",
        "thumbnail_image",
        "is_document_image",
    )

    def get_queryset(self):
        ids = self.normalize_ids(value=self.get_parameter(key="ids"))
        product_ids = self.normalize_ids(value=self.get_parameter(key="product"))
        sales_channel = self.resolve_sales_channel()

        queryset = MediaProductThrough.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            media__type=self.media_type,
        ).select_related(
            "product",
            "media",
            "media__document_type",
            "sales_channel",
        )

        if sales_channel is None:
            queryset = queryset.filter(sales_channel__isnull=True)
        else:
            queryset = queryset.filter(sales_channel=sales_channel)

        if ids:
            queryset = queryset.filter(media_id__in=ids)
        if product_ids:
            queryset = queryset.filter(product_id__in=product_ids)

        return queryset.order_by("product_id", "sort_order", "media_id")

    def build_media_payload(self, *, assignment):
        raise NotImplementedError

    def get_payload(self):
        include_product_sku = self.include_column(key="product_sku") or to_bool(
            value=self.get_parameter(key="add_product_sku"),
        )
        include_product_data = self.include_column(key="product_data")
        include_title = self.include_column(key="title") or to_bool(
            value=self.get_parameter(key="add_title"),
        )
        include_description = self.include_column(key="description") or to_bool(
            value=self.get_parameter(key="add_description"),
        )
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)

        payload = []
        for index, assignment in enumerate(self.iterate_queryset(queryset=queryset), start=1):
            media = assignment.media
            row = self.build_media_payload(assignment=assignment)

            if self.include_column(key="type"):
                row["type"] = media.image_type if media.type == Media.IMAGE else media.type

            if include_title and media.title:
                row["title"] = media.title
            if include_description and media.description:
                row["description"] = media.description
            if include_product_data:
                row["product_data"] = build_product_stub(product=assignment.product)
            if include_product_sku:
                row["product_sku"] = assignment.product.sku
            if self.include_column(key="sort_order"):
                row["sort_order"] = assignment.sort_order

            payload.append(row)
            self.update_progress(processed=index, total_records=total_records)

        return payload


class ImagesExportFactory(BaseMediaExportFactory):
    kind = "images"
    media_type = Media.IMAGE

    def build_media_payload(self, *, assignment):
        row = {
            "image_url": assignment.media.image_url(),
        }
        if self.include_column(key="is_main_image"):
            row["is_main_image"] = assignment.is_main_image
        return row


class DocumentsExportFactory(BaseMediaExportFactory):
    kind = "documents"
    media_type = Media.FILE

    def build_media_payload(self, *, assignment):
        media = assignment.media
        row = {
            "document_url": media.get_real_document_file(),
        }
        if self.include_column(key="document_type") and media.document_type_id:
            row["document_type"] = media.document_type.code or media.document_type.name
        if self.include_column(key="document_language"):
            row["document_language"] = media.document_language
        if self.include_column(key="thumbnail_image"):
            row["thumbnail_image"] = media.document_image_thumbnail_url()
        if self.include_column(key="is_document_image"):
            row["is_document_image"] = media.is_document_image
        return row


class VideosExportFactory(BaseMediaExportFactory):
    kind = "videos"
    media_type = Media.VIDEO

    def build_media_payload(self, *, assignment):
        return {
            "video_url": assignment.media.video_url,
        }
