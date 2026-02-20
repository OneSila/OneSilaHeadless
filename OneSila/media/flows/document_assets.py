from media.factories import DocumentAssetsFactory


def generate_document_assets_flow(*, media_instance):
    factory = DocumentAssetsFactory(media_instance=media_instance)
    factory.run()
