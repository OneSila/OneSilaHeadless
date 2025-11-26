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

PROPERTIES_USED_IN_PRODUCTS_QUERY = """
query Properties($usedInProducts: Boolean!) {
  properties(filters: {usedInProducts: $usedInProducts}) {
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

PROPERTY_SELECT_VALUES_USED_IN_PRODUCTS_QUERY = """
query PropertySelectValues($usedInProducts: Boolean!) {
  propertySelectValues(filters: {usedInProducts: $usedInProducts}) {
    edges { node { id } }
  }
}
"""
