import logging
logger = logging.getLogger(__name__)

from core.decorators import allow_soft_sanity_check_errors


@allow_soft_sanity_check_errors   
def populate_title_flow(media_instance):
    from media.factories import PopulateTitleFactory
    
    f = PopulateTitleFactory(media_instance, save=True)
    f.run()
