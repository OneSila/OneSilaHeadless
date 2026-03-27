from eancodes.schema.mutations.mutation_classes import (
    GenerateEancodesMutation,
    AssignEanCodeMutation,
    ManualAssignEanCodeMutation,
    ReleaseEanCodeMutation,
)
from eancodes.schema.types.input import (
    GenerateEancodesInput,
    EanCodePartialInput,
    AssignEancodeInput,
    ManualAssignEancodeInput,
)


def generate_eancodes():
    extensions = []
    return GenerateEancodesMutation(GenerateEancodesInput, extensions=extensions)


def assign_ean_code():
    extensions = []
    return AssignEanCodeMutation(AssignEancodeInput, extensions=extensions)


def manual_assign_ean_code():
    extensions = []
    return ManualAssignEanCodeMutation(ManualAssignEancodeInput, extensions=extensions)


def release_ean_code():
    extensions = []
    return ReleaseEanCodeMutation(EanCodePartialInput, extensions=extensions)
