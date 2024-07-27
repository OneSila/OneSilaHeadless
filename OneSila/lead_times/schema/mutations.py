from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List

from .types.types import LeadTimeType, LeadTimeTranslationType
from .types.input import LeadTimeInput, LeadTimePartialInput, \
    LeadTimeTranslationInput, LeadTimeTranslationPartialInput

from lead_times.models import LeadTimeTranslation
from lead_times.schema.types.input import LeadTimeInput
from translations.schema.mutations import TranslatableCreateMutation


def create_lead_time():
    extensions = []
    return TranslatableCreateMutation(LeadTimeInput,
        extensions=extensions,
        translation_model=LeadTimeTranslation,
        translation_field='name',
        translation_model_to_model_field='lead_time')


@type(name="Mutation")
class LeadTimesMutation:
    create_lead_time: LeadTimeType = create_lead_time()
    create_lead_times: List[LeadTimeType] = create(LeadTimeInput)
    update_lead_time: LeadTimeType = update(LeadTimePartialInput)
    delete_lead_time: LeadTimeType = delete()
    delete_lead_times: List[LeadTimeType] = delete()

    create_lead_time_translation: LeadTimeTranslationType = create(LeadTimeTranslationInput)
    create_lead_time_translations: List[LeadTimeTranslationType] = create(LeadTimeTranslationInput)
    update_lead_time_translation: LeadTimeTranslationType = update(LeadTimeTranslationPartialInput)
    delete_lead_time_translation: LeadTimeTranslationType = delete()
    delete_lead_time_translations: List[LeadTimeTranslationType] = delete()
