PROPERTIES_MISSING_MAIN_TRANSLATION_QUERY = """
query Properties($missingMainTranslation: Boolean!) {
  properties(filters: {missingMainTranslation: $missingMainTranslation}) {
    edges { node { id } }
  }
}
"""

PROPERTIES_MISSING_TRANSLATIONS_QUERY = """
query Properties($missingTranslations: Boolean!) {
  properties(filters: {missingTranslations: $missingTranslations}) {
    edges { node { id } }
  }
}
"""

PROPERTY_SELECT_VALUES_MISSING_MAIN_TRANSLATION_QUERY = """
query PropertySelectValues($missingMainTranslation: Boolean!) {
  propertySelectValues(filters: {missingMainTranslation: $missingMainTranslation}) {
    edges { node { id } }
  }
}
"""

PROPERTY_SELECT_VALUES_MISSING_TRANSLATIONS_QUERY = """
query PropertySelectValues($missingTranslations: Boolean!) {
  propertySelectValues(filters: {missingTranslations: $missingTranslations}) {
    edges { node { id } }
  }
}
"""
