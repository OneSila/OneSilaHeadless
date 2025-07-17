BATTERY_SCHEMA = {
    "battery": {
        "title": "Battery",
        "description": "Provide battery information",
        "examples": ["Alkaline"],
        "type": "array",
        "minItems": 1,
        "minUniqueItems": 1,
        "maxUniqueItems": 1,
        "selectors": ["marketplace_id"],
        "items": {
            "type": "object",
            "required": [],
            "properties": {
                "cell_composition": {
                    "title": "Battery Cell Composition",
                    "description": "Select the chemical composition of the battery cell",
                    "examples": ["NiMh"],
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["value"],
                        "properties": {
                            "value": {
                                "title": "Battery Cell Composition",
                                "description": "Select the chemical composition of the battery cell",
                                "editable": True,
                                "hidden": False,
                                "examples": ["NiMh"],
                                "type": "string",
                                "enum": [
                                    "alkaline", "lead_acid", "lithium_ion", "lithium_metal", "lithium_polymer",
                                    "NiCAD", "NiMh", "other_than_listed", "sodium_ion", "wet_alkali"
                                ],
                                "enumNames": [
                                    "Alkaline", "Lead Acid", "Lithium Ion", "Lithium Metal", "Lithium Polymer",
                                    "NiCAD", "NiMH", "Other Than Listed", "Sodium Ion", "Wet Alkali"
                                ]
                            }
                        },
                        "additionalProperties": False
                    }
                },
                "cell_composition_other_than_listed": {
                    "title": "Battery Cell Composition Other Than Listed",
                    "description": "Provide the components of the item's battery cell that are not already listed under battery cell composition.",
                    "examples": ["Silver Oxide"],
                    "type": "array",
                    "minItems": 1,
                    "minUniqueItems": 1,
                    "maxUniqueItems": 1,
                    "selectors": ["language_tag"],
                    "items": {
                        "type": "object",
                        "required": ["language_tag", "value"],
                        "properties": {
                            "value": {
                                "title": "Battery Cell Composition Other Than Listed",
                                "description": "Provide the components of the item's battery cell that are not already listed under battery cell composition.",
                                "editable": True,
                                "hidden": False,
                                "examples": ["Silver Oxide (Ag₂O)"],
                                "type": "string",
                                "maxLength": 50
                            },
                            "language_tag": {
                                "$ref": "#/$defs/language_tag"
                            }
                        },
                        "additionalProperties": False
                    }
                },
                "iec_code": {
                    "title": "Battery IEC Code",
                    "description": "Provide the item’s battery IEC code. IEC is standardized alphanumeric nomenclature based on battery size & type available on battery itself.",
                    "examples": ["CR2320"],
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["value"],
                        "properties": {
                            "value": {
                                "title": "Battery IEC Code",
                                "description": "Provide the item’s battery IEC code. IEC is standardized alphanumeric nomenclature based on battery size & type available on battery itself.",
                                "editable": True,
                                "hidden": False,
                                "examples": ["CR2320"],
                                "type": "string",
                                "enum": ["14500", "18650", "2cr11108_2cr1_3n", "2cr5", "2r10", "cr2320"],
                                "enumNames": ["14500", "18650", "2CR11108 2CR1/3N", "2CR5", "2R10", "CR2320"]
                            }
                        },
                        "additionalProperties": False
                    }
                },
                "marketplace_id": {
                    "$ref": "#/$defs/marketplace_id"
                },
                "weight": {
                    "title": "Battery Weight",
                    "description": "Provide the total net weight of the batteries included. This is the weight of the standalone batteries not including packaging or the device it may be used in",
                    "examples": ["2.5 Grams"],
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["unit", "value"],
                        "properties": {
                            "value": {
                                "title": "Battery Weight",
                                "description": "Provide the total net weight (numeric value) of the batteries included. This is the weight of the standalone batteries not including packaging or the device it may be used in.",
                                "editable": True,
                                "hidden": False,
                                "examples": ["2.5"],
                                "type": "number",
                                "minimum": 0,
                                "maxLength": 5000
                            },
                            "unit": {
                                "title": "Battery Weight Unit",
                                "description": "Select the corresponding unit",
                                "editable": True,
                                "hidden": False,
                                "examples": ["Grams"],
                                "type": "string",
                                "enum": ["grams", "kilograms", "milligrams", "ounces", "pounds"],
                                "enumNames": ["Grams", "Kilograms", "Milligrams", "Ounces", "Pounds"]
                            }
                        },
                        "additionalProperties": False
                    }
                }
            },
            "additionalProperties": False
        }
    }
}

NUM_BATTERIES_SCHEMA = {
    "num_batteries": {
        "title": "Number of Batteries",
        "description": "...",
        "examples": ["1 AA, 2 AAA"],
        "type": "array",
        "minItems": 1,
        "minUniqueItems": 1,
        "maxUniqueItems": 1000,
        "selectors": ["marketplace_id", "type"],
        "items": {
            "type": "object",
            "required": ["quantity", "type"],
            "properties": {
                "marketplace_id": {
                    "$ref": "#/$defs/marketplace_id"
                },
                "quantity": {
                    "title": "Number of Batteries",
                    "description": "...",
                    "editable": True,
                    "hidden": False,
                    "examples": ["1, 4"],
                    "type": "integer",
                    "minimum": 0
                },
                "type": {
                    "title": "Battery Type",
                    "description": "...",
                    "editable": True,
                    "hidden": False,
                    "examples": ["12 V"],
                    "type": "string",
                    "enum": ["12v", "9v", "a", "aa", "aaa", "aaaa", "c", "d", "nonstandard_battery"],
                    "enumNames": ["12V", "9V", "A", "AA", "AAA", "AAAA", "C", "D", "Nonstandard Battery"]
                }
            },
            "additionalProperties": False
        }
    }
}

NUMBER_OF_LITHIUM_METAL_CELLS_SCHEMA = {
    "number_of_lithium_metal_cells": {
        "title": "Number of Lithium Metal Cells",
        "description": "Specify the total number of Lithium Metal cells in the product where the cell isn't contained in an encased battery (e.g. coin cells)",
        "examples": ["7"],
        "type": "array",
        "minItems": 1,
        "minUniqueItems": 1,
        "maxUniqueItems": 1,
        "selectors": ["marketplace_id"],
        "items": {
            "type": "object",
            "required": ["value"],
            "properties": {
                "value": {
                    "title": "Number of Lithium Metal Cells",
                    "description": "Specify the total number of Lithium Metal cells in the product where the cell isn't contained in an encased battery (e.g. coin cells)",
                    "editable": True,
                    "hidden": False,
                    "examples": ["7"],
                    "type": "integer",
                    "minimum": 0
                },
                "marketplace_id": {
                    "$ref": "#/$defs/marketplace_id"
                }
            },
            "additionalProperties": False
        }
    }
}

CUSTOMER_PACKAGE_TYPE_SCHEMA = {
    "customer_package_type": {
        "title": "Customer Package Type",
        "description": "Provide the products package type",
        "examples": [
            "Standard Packaging"
        ],
        "type": "array",
        "minItems": 1,
        "minUniqueItems": 1,
        "maxUniqueItems": 1,
        "selectors": [
            "marketplace_id",
            "language_tag"
        ],
        "items": {
            "type": "object",
            "required": [
                "language_tag",
                "value"
            ],
            "properties": {
                "value": {
                    "title": "Customer Package Type",
                    "description": "Provide the products package type",
                    "editable": True,
                    "hidden": False,
                    "examples": [
                        "Standard Packaging"
                    ],
                    "type": "string",
                    "maxLength": 2176
                },
                "language_tag": {
                    "$ref": "#/$defs/language_tag"
                },
                "marketplace_id": {
                    "$ref": "#/$defs/marketplace_id"
                }
            },
            "additionalProperties": False
        }
    }
}

POWER_PLUG_TYPE_SCHEMA = {
    "power_plug_type": {
        "title": "Power Plug Type",
        "description": "Provide the type of electrical connector used to supply power to the air purifier, indicating compatibility with different outlet standards.",
        "examples": [
            "Type A - 2 pin (North American), Type C - 2 pin (Europlug)"
        ],
        "type": "array",
        "minItems": 1,
        "minUniqueItems": 1,
        "maxUniqueItems": 4,
        "selectors": [
            "marketplace_id"
        ],
        "items": {
            "type": "object",
            "required": [
                "value"
            ],
            "properties": {
                "value": {
                    "title": "Power Plug",
                    "description": "Provide the type of electrical connector used to supply power to the air purifier, indicating compatibility with different outlet standards.",
                    "editable": False,
                    "hidden": False,
                    "examples": [
                        "Type G, CEE 7/16 Europlug"
                    ],
                    "type": "string",
                    "enum": [
                        "16_a_5_pin",
                        "32_a_5_pin",
                        "type_cee716_europlug",
                        "type_bs_2pin_uk",
                        "no_plug",
                        "type_a_2pin_jp",
                        "type_a_2pin_na_jp",
                        "type_a_2pin_na",
                        "type_b_3pin_jp",
                        "type_b_3pin_na_jp",
                        "type_b_3pin_na",
                        "type_c_2pin_eu",
                        "type_cef_2pin_eu",
                        "type_d_3pin_in",
                        "type_e_2pin_fr",
                        "type_ef_2pin_eu",
                        "type_f_2pin_de_es",
                        "type_f_2pin_de",
                        "type_g_3pin_uk",
                        "type_h_3pin_il",
                        "type_i_3pin_au_cn",
                        "type_i_3pin_au",
                        "type_j_3pin_ch",
                        "type_k_3pin_dk",
                        "type_l_3pin_it",
                        "type_m_3pin_za",
                        "type_n_3pin_br"
                    ],
                    "enumNames": [
                        "16A 5 Pin",
                        "32A 5 Pin",
                        "CEE 7/16 Europlug",
                        "Moulded 2-pin BS 4573 UK Shaver plug",
                        "No Plug",
                        "Type A - 2 pin (Japanese)",
                        "Type A - 2 pin (North American & Japanese)",
                        "Type A - 2 pin (North American)",
                        "Type B - 3 pin (Japanese)",
                        "Type B - 3 pin (North American & Japanese)",
                        "Type B - 3 pin (North American)",
                        "Type C",
                        "Type C/EF - 2 pin (Europlug/FR-DE Hybrid)",
                        "Type D",
                        "Type E - 2 pin (French)",
                        "Type E / F - 2 pin (EU Hybrid)",
                        "Type F - 2 pin (German & Spanish)",
                        "Type F - 2 pin (German)",
                        "Type G",
                        "Type H",
                        "Type I - 3 pin (Australian & Chinese)",
                        "Type I - 3 pin (Australian)",
                        "Type J",
                        "Type K",
                        "Type L",
                        "Type M",
                        "Type N"
                    ]
                },
                "marketplace_id": {
                    "$ref": "#/$defs/marketplace_id"
                }
            },
            "additionalProperties": False
        }
    }
}

CONTROLLER_TYPE_SCHEMA = {
    "controller_type": {
        "title": "Controller Type",
        "description": "Provide the type of device or app used to control the item, like a smartphone app or computer software.",
        "examples": ["Wimoto, Nexia, B 180"],
        "type": "array",
        "minItems": 1,
        "minUniqueItems": 1,
        "maxUniqueItems": 5,
        "selectors": ["marketplace_id", "language_tag"],
        "items": {
            "type": "object",
            "required": ["language_tag", "value"],
            "properties": {
                "value": {
                    "title": "Controller Type",
                    "description": "Provide the type of control system used to operate the air purifier, indicating how users can adjust settings and functions.",
                    "editable": True,
                    "hidden": False,
                    "examples": ["Wimoto, Nexia, B 180"],
                    "type": "string",
                    "maxLength": 1542,
                    "anyOf": [
                        {"type": "string"},
                        {
                            "type": "string",
                            "enum": [
                                "Amazon Alexa", "Android", "Apple HomeKit", "Button Control", "Control4",
                                "Foot Control", "Google Assistant", "Govee Home", "Hand Control", "IFTTT",
                                "Insteon", "iOS", "iPadOS", "Iris", "Jog Dial", "Mechanical Knob", "Nexia",
                                "Remote Control", "Ring", "SmartThings", "Vera", "VeSync", "Vivint", "WeMo", "Wink"
                            ],
                            "enumNames": [
                                "Amazon Alexa", "Android", "Apple HomeKit", "Button Control", "Control4",
                                "Foot Control", "Google Assistant", "Govee Home", "Hand Control", "IFTTT",
                                "Insteon", "iOS", "iPadOS", "Iris", "Jog Dial", "Mechanical Knob", "Nexia",
                                "Remote Control", "Ring", "SmartThings", "Vera", "VeSync", "Vivint", "WeMo", "Wink"
                            ]
                        }
                    ]
                },
                "language_tag": {
                    "$ref": "#/$defs/language_tag"
                },
                "marketplace_id": {
                    "$ref": "#/$defs/marketplace_id"
                }
            },
            "additionalProperties": False
        }
    }
}

PRODUCT_SITE_LAUNCH_DATE_SCHEMA = {
    "product_site_launch_date": {
        "title": "Product Site Launch Date",
        "description": "Provide the date (YYYYMMDD) the product launches and should first be shown on the Amazon website, this field should not be used to create pre-orders",
        "examples": ["2017-07-20"],
        "type": "array",
        "minItems": 1,
        "minUniqueItems": 1,
        "maxUniqueItems": 1,
        "selectors": ["marketplace_id"],
        "items": {
            "type": "object",
            "required": ["value"],
            "properties": {
                "marketplace_id": {
                    "$ref": "#/$defs/marketplace_id"
                },
                "value": {
                    "title": "Product Site Launch Date",
                    "description": "Provide the date (YYYYMMDD) the product launches and should first be shown on the Amazon website, this field should not be used to create pre-orders",
                    "editable": True,
                    "hidden": False,
                    "examples": ["2017-07-20"],
                    "type": "string",
                    "oneOf": [
                        {"type": "string", "format": "date"},
                        {"type": "string", "format": "date-time"}
                    ]
                }
            },
            "additionalProperties": False
        }
    }
}

COLOR_SCHEMA = {
    "color": {
        "title": "Colour",
        "description": "Provide the colour of the product",
        "examples": ["Cranberry"],
        "type": "array",
        "minItems": 1,
        "minUniqueItems": 1,
        "maxUniqueItems": 1,
        "selectors": ["marketplace_id", "language_tag"],
        "items": {
            "type": "object",
            "required": ["language_tag"],
            "properties": {
                "standardized_values": {
                    "title": "Colour Map",
                    "description": "Select the most dominant colour of the product.",
                    "editable": True,
                    "hidden": False,
                    "examples": ["Red"],
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {
                        "type": "string",
                        "anyOf": [
                            {"type": "string"},
                            {
                                "type": "string",
                                "enum": [
                                    "Beige", "Black", "Blue", "Bronze", "Brown", "Clear",
                                    "Gold", "Green", "Grey", "Metallic", "Multicolor", "Off White",
                                    "Orange", "Pink", "Purple", "Red", "Silver", "Turquoise", "White", "Yellow"
                                ],
                                "enumNames": [
                                    "Beige", "Black", "Blue", "Bronze", "Brown", "Clear",
                                    "Gold", "Green", "Grey", "Metallic", "Multicolor", "Off White",
                                    "Orange", "Pink", "Purple", "Red", "Silver", "Turquoise", "White", "Yellow"
                                ]
                            }
                        ]
                    }
                },
                "value": {
                    "title": "Colour",
                    "description": "Provide the colour of the product",
                    "editable": True,
                    "hidden": False,
                    "examples": ["Cranberry"],
                    "type": "string",
                    "minLength": 0,
                    "maxLength": 70
                },
                "language_tag": {
                    "$ref": "#/$defs/language_tag"
                },
                "marketplace_id": {
                    "$ref": "#/$defs/marketplace_id"
                }
            },
            "additionalProperties": False
        }
    }
}

