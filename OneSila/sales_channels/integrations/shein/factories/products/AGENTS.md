Full product publish or edit payload schema:

```json
{
  "brand_code": {
    "type": "string",
    "required": false,
    "description": "Brand code available for the store. Mandatory for some merchants depending on Product Release Specification (field_key=brand_code & required=true). Code must be obtained from Store Brand List API. When editing, omitting this field clears the value."
  },
  "category_id": {
    "type": "integer",
    "required": true,
    "description": "Last-level category ID. Obtained via 'Store Query Product Last-Level Category' API (last_category=true)."
  },
  "product_type_id": {
    "type": "integer",
    "required": false,
    "description": "Product type ID. Obtained via 'Shop Query Product Final Classification' API."
  },
  "source_system": {
    "type": "string",
    "required": false,
    "description": "Source system identifier. Fixed value: OpenAPI."
  },
  "spu_name": {
    "type": "string",
    "required": false,
    "description": "Platform-generated unique SPU code. Do not send when creating new SPUs or adding SKCs; mandatory when editing existing SPUs."
  },
  "supplier_code": {
    "type": "string",
    "required": false,
    "description": "Merchant item number at main specification granularity, up to 200 characters. See supplier_code FAQ for details."
  },
  "suit_flag": {
    "type": "string",
    "required": false,
    "description": "Whether it is a set. Enumerated values: 1 = Yes, 0 = No. API does not currently support sets, so this must be 0 or omitted (default 0)."
  },
  "is_spu_pic": {
    "type": "boolean",
    "required": false,
    "description": "Whether to use the new SPU-level image solution. true = new solution, false = old solution. Default false if not provided."
  },

  "fill_configuration_info": {
    "type": "object",
    "description": "Product information filling rules. Indicates whether new or old filling scheme is used for release validation.",
    "properties": {
      "filled_quantity_to_sku": {
        "type": "boolean",
        "required": false,
        "description": "Whether quantity is filled at the SKU level. Only valid for categories where field_key='quantity_info' and show=true in release specs. If true, sku_list.quantity_info must be passed. Defaults to false if omitted."
      },
      "fill_configuration_tags": {
        "type": "array",
        "required": false,
        "description": "Tags indicating which specific information was filled in this input. Currently supported values: 'PACKAGE_TYPE_TO_SKU' (SKU-level package_type).",
        "items": {
          "type": "string",
          "required": false,
          "description": "Tag name, e.g. 'PACKAGE_TYPE_TO_SKU'."
        }
      }
    }
  },

  "image_info": {
    "type": "object",
    "description": "SPU-level image information. Only used when is_spu_pic=true. Omitting this field in edit operations clears SPU image data.",
    "properties": {
      "image_group_code": {
        "type": "string",
        "required": false,
        "description": "SPU image group code. Not allowed when creating new SPUs or adding SKCs; mandatory in some edit scenarios. Obtain via SPU detail query."
      },
      "image_info_list": {
        "type": "array",
        "required": false,
        "description": "List of SPU-level images. Image types, quantity, and size requirements follow the Product Image Plan.",
        "items": {
          "type": "object",
          "description": "Single SPU image entry.",
          "properties": {
            "image_item_id": {
              "type": "integer",
              "required": false,
              "description": "Platform-generated unique image code. Not required for new SPUs/added SKCs; mandatory in some edit scenarios (see FAQ examples)."
            },
            "image_sort": {
              "type": "integer",
              "required": false,
              "description": "Image sequence number within the same image group. Sequence values in the group must be unique. If image_type=1 (main image), sort must be 1."
            },
            "image_type": {
              "type": "integer",
              "required": false,
              "description": "Image type. Enumerated: 1=Main image, 2=Detail image, 5=Block image, 6=Color block image. See Product Image Plan for requirements."
            },
            "image_url": {
              "type": "string",
              "required": false,
              "description": "SHEIN-format image URL. Must be obtained via External link conversion or Local image upload APIs."
            }
          }
        }
      }
    }
  },

  "multi_language_desc_list": {
    "type": "array",
    "description": "Product description list supporting multiple languages. Omitting this field during edit clears existing descriptions.",
    "items": {
      "type": "object",
      "description": "Single language entry for description.",
      "properties": {
        "language": {
          "type": "string",
          "required": true,
          "description": "Language code. Default language must be provided if any description is sent. Default language is given by Product Release Specifications (default_language)."
        },
        "name": {
          "type": "string",
          "required": true,
          "description": "Multilingual description text, up to 5000 characters. Must not contain HTML, emojis, or special Unicode symbols (emoji disallowed by regex)."
        }
      }
    }
  },

  "multi_language_name_list": {
    "type": "array",
    "description": "Product name list supporting multiple languages.",
    "items": {
      "type": "object",
      "description": "Single language entry for product name.",
      "properties": {
        "language": {
          "type": "string",
          "required": true,
          "description": "Language code. Default language must be provided if any name is sent (see Product Release Specifications default_language)."
        },
        "name": {
          "type": "string",
          "required": true,
          "description": "Product name in this language, up to 1000 characters. Emojis are not supported."
        }
      }
    }
  },

  "product_attribute_list": {
    "type": "array",
    "description": "List of product attributes (attribute_type=3/4 only). Omitting this field during edit clears attribute data.",
    "items": {
      "type": "object",
      "description": "Single product attribute entry.",
      "properties": {
        "attribute_extra_value": {
          "type": "string",
          "required": false,
          "description": "Manual attribute value. Used when attribute_mode=0/4 (manual input). Only positive integers are supported. For attribute_type=3 & attribute_mode=4, sum of all manual values for the same attribute must be 100."
        },
        "attribute_id": {
          "type": "integer",
          "required": true,
          "description": "Attribute ID. Only attributes with attribute_type=3 or 4 can be used. Mandatory attributes are determined via attribute_status=3 or by related attribute rules."
        },
        "attribute_value_id": {
          "type": "integer",
          "required": true,
          "description": "Attribute value ID. Required when attribute_mode=1/3/4. For mode 3 (single-select), only one value allowed; for modes 1/4 (multi-select), multiple values are allowed as separate records."
        }
      }
    }
  },

  "site_list": {
    "type": "array",
    "description": "Publishing site configuration. Required when creating new products/adding SKCs; must not be sent when editing.",
    "items": {
      "type": "object",
      "description": "Single site config entry.",
      "properties": {
        "main_site": {
          "type": "string",
          "required": false,
          "description": "Main site identifier. Value corresponds to mainSite from 'Query store sellable sites and site currencies' API."
        },
        "sub_site_list": {
          "type": "array",
          "required": false,
          "description": "List of subsites for publication. Required for new products. Values are siteAbbr from 'Query store available sites and site currencies' API.",
          "items": {
            "type": "string",
            "required": false,
            "description": "Subsite abbreviation (siteAbbr)."
          }
        }
      }
    }
  },

  "size_attribute_list": {
    "type": "array",
    "description": "Size attributes (size chart). Only attributes with attribute_type=2 are allowed. Omitting this field during edit clears size attributes.",
    "items": {
      "type": "object",
      "description": "Single size attribute entry.",
      "properties": {
        "attribute_id": {
          "type": "integer",
          "required": false,
          "description": "Size attribute ID (attribute_type=2). Some size attributes are mandatory (attribute_status=3) per Store Available Attributes API."
        },
        "attribute_value_id": {
          "type": "integer",
          "required": false,
          "description": "Size attribute value ID. For size attributes, the value is usually supplied via attribute_extra_value instead."
        },
        "attribute_extra_value": {
          "type": "string",
          "required": false,
          "description": "Manual size value. Used when attribute_mode=0/4, supports positive integers only."
        },
        "relate_sale_attribute_id": {
          "type": "integer",
          "required": false,
          "description": "Associated sales attribute ID for building a size chart (e.g., size attribute + size sales attribute). Only SKU-level sales attributes can be associated."
        },
        "relate_sale_attribute_value_id": {
          "type": "integer",
          "required": false,
          "description": "Associated sales attribute value ID for the size chart. Only SKU-level attributes can be associated."
        },
        "relate_sale_attribute_value": {
          "type": "string",
          "required": false,
          "description": "Associated custom sales attribute value. Used when the SKU sales attribute value is custom; must exactly match the SKU attribute value content."
        }
      }
    }
  },

  "skc_list": {
    "type": "array",
    "description": "List of SKCs (style-color combinations) under the SPU. A maximum of 40 SKCs per SPU.",
    "items": {
      "type": "object",
      "description": "Single SKC entry.",
      "properties": {
        "image_info": {
          "type": "object",
          "description": "SKC-level image information. Omitting in edit clears SKC images.",
          "properties": {
            "image_group_code": {
              "type": "string",
              "required": false,
              "description": "SKC image group code. Not allowed when creating/adding SKCs; mandatory when editing existing SKCs. Obtained via SPU detail query."
            },
            "image_info_list": {
              "type": "array",
              "required": true,
              "description": "SKC image list. Requirements differ between old and new image plans.",
              "items": {
                "type": "object",
                "description": "Single SKC image entry.",
                "properties": {
                  "image_item_id": {
                    "type": "integer",
                    "required": false,
                    "description": "Platform-generated unique image code. Not required for new SKCs; mandatory in some edit scenarios (see FAQ examples)."
                  },
                  "image_sort": {
                    "type": "integer",
                    "required": true,
                    "description": "Image sequence number. Must be unique within the same image group. Image with image_type=1 must have sort=1."
                  },
                  "image_type": {
                    "type": "integer",
                    "required": true,
                    "description": "Image type. 1=Main image (max 1), 2=Detail image (max 10), 5=Square image, 6=Color block image (mandatory for multiple SKCs)."
                  },
                  "image_url": {
                    "type": "string",
                    "required": true,
                    "description": "SHEIN-format image URL, from External link conversion or Local image upload APIs."
                  }
                }
              }
            }
          }
        },

        "sale_attribute": {
          "type": "object",
          "description": "SKC sales attribute (e.g., color). Required when creating new products or adding SKCs. Mandatory for edit but not modifiable.",
          "properties": {
            "attribute_id": {
              "type": "integer",
              "required": true,
              "description": "Sales attribute ID (attribute_type=1 and attribute_label=1). Mandatory sales attributes have attribute_status=3 in Store Available Attributes."
            },
            "attribute_value_id": {
              "type": "integer",
              "required": true,
              "description": "Sales attribute value ID for the SKC."
            },
            "custom_attribute_value": {
              "type": "string",
              "required": false,
              "description": "Custom sales attribute value. Only allowed if the attribute supports custom values (see get-custom-attribute-permission-config). Up to 50 characters; half-width symbols only; no Unicode emoji."
            },
            "language": {
              "type": "string",
              "required": false,
              "description": "Language code for the custom attribute value. Supported: en, zh-cn, fr, es, it. If not provided, platform may auto-translate."
            }
          }
        },

        "skc_name": {
          "type": "string",
          "required": false,
          "description": "Unique SKC code generated by the platform. Not allowed in add scenario; mandatory when editing existing published SKC, not required for new SKC additions."
        },
        "supplier_code": {
          "type": "string",
          "required": true,
          "description": "Merchant-side SKC-level item number, up to 200 characters."
        },
        "skc_title": {
          "type": "string",
          "required": false,
          "description": "SKC-level product title. Mandatory only for some merchants when field_key='skc_title' & required=true & show=true in Product Publishing Specification. Default-language only. Omission in edit clears the value."
        },

        "sku_list": {
          "type": "array",
          "required": true,
          "description": "List of SKUs under this SKC (max 200). Even if there is no real SKU, sku_list must exist (sales attributes may be blank).",
          "items": {
            "type": "object",
            "description": "Single SKU entry.",
            "properties": {
              "cost_info": {
                "type": "object",
                "description": "SKU supply price (semi-managed/fully managed). Required for new/added SKUs in those modes; cannot be sent during edit.",
                "properties": {
                  "cost_price": {
                    "type": "string",
                    "required": false,
                    "description": "Supply price. Number between 0 and 100000, with up to 2 decimal places."
                  },
                  "currency": {
                    "type": "string",
                    "required": false,
                    "description": "Currency abbreviation for supply price. Supported currencies are given in Product Release Specification."
                  }
                }
              },

              "height": {
                "type": "string",
                "required": true,
                "description": "Package-inclusive height in cm. Positive number, up to 2 decimal places."
              },
              "length": {
                "type": "string",
                "required": true,
                "description": "Package-inclusive length in cm. Positive number, up to 2 decimal places."
              },
              "width": {
                "type": "string",
                "required": true,
                "description": "Package-inclusive width in cm. Positive number, up to 2 decimal places."
              },
              "weight": {
                "type": "integer",
                "required": true,
                "description": "Package-inclusive weight in grams. Positive integer; 0 not allowed."
              },

              "mall_state": {
                "type": "integer",
                "required": true,
                "description": "SKU mall sales status. 1=On sale, 2=Off sale. If set to off sale, stock quantity is not saved and appears empty in the merchant backend."
              },

              "sku_code": {
                "type": "string",
                "required": false,
                "description": "Unique platform SKU code. Not allowed for new SKU creation; required when editing an existing SKU."
              },
              "stop_purchase": {
                "type": "integer",
                "required": false,
                "description": "Purchase status (exclusive & mandatory use only). 1 = Available, 2 = Unavailable."
              },

              "image_info": {
                "type": "object",
                "description": "SKU-level image info. From Sept 25, all products can upload SKU images when listing (1 image). Omitting in edit clears SKU image.",
                "properties": {
                  "image_group_code": {
                    "type": "string",
                    "required": false,
                    "description": "SKU image group code. Not allowed for new SKCs; mandatory for editing in some cases. Obtained via SPU detail query."
                  },
                  "image_info_list": {
                    "type": "array",
                    "required": false,
                    "description": "List of SKU images.",
                    "items": {
                      "type": "object",
                      "description": "Single SKU image entry.",
                      "properties": {
                        "image_item_id": {
                          "type": "integer",
                          "required": false,
                          "description": "Platform-generated unique image code. Not required for new images; mandatory in some edit scenarios."
                        },
                        "image_sort": {
                          "type": "integer",
                          "required": false,
                          "description": "Image sequence number within image group. Unique per group. If image_type=1, sort must be 1."
                        },
                        "image_type": {
                          "type": "integer",
                          "required": false,
                          "description": "Image type. For SKU images only image_type=1 is supported. See image requirements for dimensions and formats."
                        },
                        "image_url": {
                          "type": "string",
                          "required": false,
                          "description": "SHEIN-format image URL from External link conversion or Local image upload APIs."
                        }
                      }
                    }
                  }
                }
              },

              "supplier_sku": {
                "type": "string",
                "required": true,
                "description": "Merchant-maintained SKU code. Must be unique per store (one supplier_sku per platform SKU), up to 200 characters. Uniqueness can be checked via check-supplierSku-repeated API."
              },

              "supplier_barcode": {
                "type": "object",
                "description": "Supplier barcode info. Enabled only for some merchants per publish-fill-in-standard API (show=true for supplier_barcode). In updates: null=do not update, empty string=\"\"=clear, non-empty=overwrite.",
                "properties": {
                  "barcode": {
                    "type": "string",
                    "required": false,
                    "description": "Product barcode. Only numeric characters, up to 32 digits. Must be unique among SKUs under the same SKC."
                  },
                  "barcode_type": {
                    "type": "string",
                    "required": false,
                    "description": "Barcode type. Enumerated: 'EAN', 'UPC'."
                  }
                }
              },

              "competing_product_link": {
                "type": "string",
                "required": false,
                "description": "Reference product URL. Required for some merchants (field_key='reference_product_link' & required=true & show=true). Max length 300. Omission on edit clears value."
              },

              "price_info_list": {
                "type": "array",
                "required": true,
                "description": "Price information per listing site (self-operation & POP). Required for new/added SKUs; cannot be sent during edit. Price updates use separate 'Update product price' API.",
                "items": {
                  "type": "object",
                  "description": "Single price entry per sub-site.",
                  "properties": {
                    "base_price": {
                      "type": "number",
                      "required": true,
                      "description": "Original price. Number with up to 2 decimal places (JPY: no decimals). Must be greater than special_price if special_price is set."
                    },
                    "currency": {
                      "type": "string",
                      "required": true,
                      "description": "Currency abbreviation. Site-bound (e.g., US site uses USD). Obtainable via 'Query Site Currency' API."
                    },
                    "special_price": {
                      "type": "number",
                      "required": false,
                      "description": "Special/discount price. Number with up to 2 decimals (JPY: no decimals). Must be less than original price."
                    },
                    "sub_site": {
                      "type": "string",
                      "required": true,
                      "description": "Sub-site identifier (site_abbr) where this price applies. Obtainable via 'Query Site Currency' API."
                    }
                  }
                }
              },

              "sale_attribute_list": {
                "type": "array",
                "required": false,
                "description": "List of SKU-level sales attributes (variant options). Only attributes with attribute_type=1 and attribute_label=0/1 allowed. Up to 2 attributes per SKU. Must be consistent across SKCs. Required for new/added SKUs; immutable after approval.",
                "items": {
                  "type": "object",
                  "description": "Single SKU sales attribute entry.",
                  "properties": {
                    "attribute_id": {
                      "type": "integer",
                      "required": false,
                      "description": "Sales attribute ID."
                    },
                    "attribute_value_id": {
                      "type": "integer",
                      "required": false,
                      "description": "Sales attribute value ID."
                    },
                    "custom_attribute_value": {
                      "type": "string",
                      "required": false,
                      "description": "Custom attribute value. Only allowed if attribute supports custom values (see get-custom-attribute-permission-config). Up to 50 characters; half-width symbols only; no Unicode emoji."
                    },
                    "language": {
                      "type": "string",
                      "required": false,
                      "description": "Language code of the custom attribute value. Supported: en, zh-cn, fr, es, it. System translation may be applied if ERP does not provide all languages."
                    }
                  }
                }
              },

              "stock_info_list": {
                "type": "array",
                "required": true,
                "description": "Inventory information. Required for new/added SKUs; inventory updates use dedicated stock APIs.",
                "items": {
                  "type": "object",
                  "description": "Single stock entry.",
                  "properties": {
                    "inventory_num": {
                      "type": "integer",
                      "required": true,
                      "description": "Total stock quantity for the SKU. Can be 0."
                    },
                    "supplier_warehouse_id": {
                      "type": "string",
                      "required": false,
                      "description": "Merchant warehouse ID. Required when the store has multiple warehouses. Obtainable via Merchant Warehouse List API."
                    },
                    "supplier_warehouse_name": {
                      "type": "string",
                      "required": false,
                      "description": "Merchant warehouse name, from Merchant Warehouse List API."
                    }
                  }
                }
              },

              "quantity_info": {
                "type": "object",
                "description": "SKU-level quantity information. Used only when filled_quantity_to_sku=true in fill_configuration_info.",
                "properties": {
                  "quantity_type": {
                    "type": "integer",
                    "required": false,
                    "description": "Quantity type. 1=Single piece; 2=Multiple pieces of the same product. Quantity of approved SKUs cannot be modified."
                  },
                  "quantity_unit": {
                    "type": "integer",
                    "required": false,
                    "description": "Quantity unit. 1=Piece; 2=Pair. Must be the same for all SKUs under the same SKC. Cannot be modified after approval."
                  },
                  "quantity": {
                    "type": "integer",
                    "required": false,
                    "description": "Quantity value. Quantity information of approved SKUs cannot be modified."
                  }
                }
              },

              "package_type": {
                "type": "string",
                "required": false,
                "description": "SKU-level packaging type. Required if fill_configuration_tags contains PACKAGE_TYPE_TO_SKU. Values: 0=Clear, 1=Soft+soft, 2=Soft+hard, 3=Hard, 4=Vacuum."
              },

              "minimum_stock_quantity": {
                "type": "string",
                "required": false,
                "description": "Minimum stock quantity. Integer in range [1, 1000000]. Whether it can be passed depends on Product Release Specification (field_key='minimum_stock_quantity')."
              }
            }
          }
        },

        "suggested_retail_price": {
          "type": "object",
          "description": "Suggested retail price. Only available for some merchants (field_key='suggest_price'). Can be sent for new/added SKCs, not in edit.",
          "properties": {
            "currency": {
              "type": "string",
              "required": false,
              "description": "Currency abbreviation. Supported currencies listed in Product Release Specifications (JPY not supported currently; USD may be used temporarily)."
            },
            "price": {
              "type": "number",
              "required": false,
              "description": "Suggested retail price with up to 2 decimal places (yen has no decimals)."
            }
          }
        },

        "site_detail_image_info_list": {
          "type": "array",
          "description": "Site-specific detail images (3:4 ratio, >900px, up to 10 images). If field_key='product_detail_pic' has show=false, images cannot be uploaded.",
          "items": {
            "type": "object",
            "description": "Detail image group entry for specific sites.",
            "properties": {
              "image_group_code": {
                "type": "string",
                "required": false,
                "description": "Detail image group code. Not allowed for new SKCs; mandatory when updating published SKCs in edit (unless review failed)."
              },
              "site_abbr_list": {
                "type": "array",
                "required": false,
                "description": "List of sites (abbreviations) where these detail images apply.",
                "items": {
                  "type": "string",
                  "required": false,
                  "description": "Site abbreviation (site_abbr)."
                }
              },
              "image_info_list": {
                "type": "array",
                "required": false,
                "description": "List of detail images for these sites.",
                "items": {
                  "type": "object",
                  "description": "Single detail image entry.",
                  "properties": {
                    "image_item_id": {
                      "type": "string",
                      "required": false,
                      "description": "Image group ID for existing detail images. Not sent for first-time uploads; required when modifying existing detail images."
                    },
                    "image_sort": {
                      "type": "integer",
                      "required": false,
                      "description": "Sort order of the detail image."
                    },
                    "image_url": {
                      "type": "string",
                      "required": false,
                      "description": "SHEIN-format image URL (type=7 in conversion). From External link conversion or Local image upload APIs."
                    }
                  }
                }
              }
            }
          }
        },

        "proof_of_stock_list": {
          "type": "array",
          "description": "Proof of stock documents (image/PDF). Required only for some merchants (field_key='proof_of_stock'). Max 1 file, size <=3MB.",
          "items": {
            "type": "object",
            "description": "Single proof-of-stock file entry.",
            "properties": {
              "file_name": {
                "type": "string",
                "required": false,
                "description": "File name."
              },
              "type": {
                "type": "string",
                "required": false,
                "description": "File type: 1=Image, 2=PDF."
              },
              "url": {
                "type": "string",
                "required": false,
                "description": "File link (SHEIN URL)."
              }
            }
          }
        },

        "shelf_require": {
          "type": "string",
          "required": false,
          "description": "Whether products must arrive at SHEIN warehouse before listing. 0=No, 1=Yes. Mandatory in full-management mode or per Product Release Specification (field_key='shelf_require')."
        },
        "shelf_way": {
          "type": "string",
          "required": false,
          "description": "Listing method. 1=Automatic listing; 2=Scheduled listing."
        },
        "hope_on_sale_date": {
          "type": "string",
          "required": false,
          "description": "Expected listing time (Beijing time) when shelf_way=2 (scheduled). Format: 'YYYY-MM-DD HH:MM:SS'. Mandatory if shelf_way=2."
        }
      }
    }
  },

  "sale_attribute_sort_list": {
    "type": "array",
    "description": "Sales attribute sorting configuration for display on product detail pages. Whether an attribute supports sorting depends on support_sale_attribute_sort in Product Release Field Specifications.",
    "items": {
      "type": "object",
      "description": "Sorting config for a single sales attribute.",
      "properties": {
        "attribute_id": {
          "type": "integer",
          "required": true,
          "description": "Attribute ID for which value order is being defined."
        },
        "in_order_attribute_value_id_list": {
          "type": "array",
          "required": false,
          "description": "List of attribute value IDs in the desired order. Controls display order on product detail page.",
          "items": {
            "type": "integer",
            "required": false,
            "description": "Attribute value ID in sorted order."
          }
        },
        "in_order_attribute_value_list": {
          "type": "array",
          "required": false,
          "description": "Sorted list of attribute values/custom value notes. Required when custom attribute values exist for the attribute.",
          "items": {
            "type": "object",
            "description": "Single entry in sorted attribute value list.",
            "properties": {
              "attribute_value_id": {
                "type": "string",
                "required": false,
                "description": "Attribute value ID (for standard values)."
              },
              "custom_attribute_value": {
                "type": "string",
                "required": false,
                "description": "Custom attribute value text. Must exactly match the text used in sales attributes."
              }
            }
          }
        }
      }
    }
  },

  "sample_info": {
    "type": "object",
    "description": "Sample information for the product. Whether it is required depends on Product Release Specifications (field_key='sample_spec'). When sample info is mandatory, outer size_attribute_list must also be provided.",
    "properties": {
      "sample_spec": {
        "type": "object",
        "description": "Sample specifications.",
        "properties": {
          "main_spec": {
            "type": "object",
            "description": "Main sales attribute info for the sample (e.g. main color).",
            "properties": {
              "attribute_id": {
                "type": "integer",
                "required": false,
                "description": "Main sales attribute ID."
              },
              "attribute_value_id": {
                "type": "integer",
                "required": false,
                "description": "Main sales attribute value ID."
              },
              "attribute_value_name": {
                "type": "string",
                "required": false,
                "description": "Custom value of the main sales attribute for the sample."
              }
            }
          },
          "sub_spec_list": {
            "type": "array",
            "description": "Secondary sales attribute info for the sample (commonly size).",
            "items": {
              "type": "object",
              "description": "Single secondary sales attribute entry.",
              "properties": {
                "attribute_id": {
                  "type": "string",
                  "required": false,
                  "description": "Secondary sales attribute ID."
                },
                "attribute_value_id": {
                  "type": "string",
                  "required": false,
                  "description": "Secondary sales attribute value ID."
                },
                "attribute_value_name": {
                  "type": "string",
                  "required": false,
                  "description": "Custom value of the secondary sales attribute."
                }
              }
            }
          }
        }
      },
      "sample_judge_type": {
        "type": "integer",
        "required": false,
        "description": "Approval type for the sample. Fixed value: 2 (bulk fabric samples)."
      },
      "reserve_sample_flag": {
        "type": "integer",
        "required": false,
        "description": "Whether the sample is retained. Fixed value: 2 (No). 1 would mean Yes."
      },
      "spot_flag": {
        "type": "integer",
        "required": false,
        "description": "Whether the item is ready-made stock. 1=Yes; 2=No."
      }
    }
  }
}

```


# SHEIN Product Model (SPU / SKC / SKU) — Practical Guide

This document explains how SHEIN product publishing works in **real terms**, with concrete examples.
It is intended for agents that generate tests, payloads, or integration code.

---

## Core Concepts

### SPU — Product Concept
- Represents the **overall product**
- Example:
  - “Basic T-Shirt”
  - “Running Shoes”
- One SPU can contain **multiple SKCs**

---

### SKC — Main Variant (Visual / Main Spec)
- Represents **ONE value of the main sales attribute**
- Usually **Color**, sometimes **Style**
- Has:
  - Its own image set
  - One required `sale_attribute` (main spec)
- Max **40 SKCs per SPU**

**Example SKCs for a T-Shirt SPU**
- Red
- Blue
- Green

> SKC is **not** size, pack, or material  
> SKC is the **primary visual selector**

---

### SKU — Actual Buyable Item
- Represents a **specific purchasable combination**
- Has:
  - Price
  - Stock
  - Weight & dimensions
  - Optional SKU-level attributes (size, pack, fit, etc.)
- Max **200 SKUs per SKC**

---

## Rule Summary (Must Not Be Violated)

- Every product **must have at least 1 SKC**
- Every SKC **must have at least 1 SKU**
- Color (or main spec) **must be SKC-level**
- Size / Pack / Fit **must be SKU-level**
- All SKUs under the same SKC **share the same main spec**
- SKUs can differ by:
  - sale attributes
  - quantity_info
  - price
  - stock
- Max **3 sales attributes total**: **1 at SKC level** (`sale_attribute`) + **up to 2 at SKU level** (`sale_attribute_list`)
- `product_attribute_list` is **SPU-level**; for configurables only include attributes **common to all variations**
- `size_attribute_list` is SPU-level; when SKUs exist, include `relate_sale_attribute_id` + `relate_sale_attribute_value_id` (omit those fields when there is no SKU-level sales attribute)
- For **multi-select attributes**, send **one entry per selected value** (do not bundle multiple IDs in a single payload item)
- `supplier_code` is mapped via the internal property `supplier_code` (TEXT) and must be set per SKC/SKU

---

## Example 1 — Simple Product (One Size, One Color)

**Product:**  
Basic T-Shirt, Red, One Size

### Structure

SPU: Basic T-Shirt  
└─ SKC: Red  
   └─ SKU: One Size  

### Key Notes
- Only **one SKC**
- Only **one SKU**
- No size attribute needed

### Example payload (simplified but valid shape)

```json
{
  "category_id": 20000000,
  "site_list": [
    {
      "main_site": "shein",
      "sub_site_list": ["shein-us"]
    }
  ],
  "multi_language_name_list": [
    { "language": "en", "name": "Basic T-Shirt" }
  ],
  "multi_language_desc_list": [
    { "language": "en", "name": "Simple red t-shirt, one size." }
  ],
  "skc_list": [
    {
      "image_info": {
        "image_info_list": [
          { "image_sort": 1, "image_type": 1, "image_url": "https://img.shein.com/example_main_square.jpg" },
          { "image_sort": 2, "image_type": 2, "image_url": "https://img.shein.com/example_detail_1.jpg" }
        ]
      },
      "sale_attribute": {
        "attribute_id": 1001,
        "attribute_value_id": 2001
      },
      "supplier_code": "TSHIRT-RED",
      "sku_list": [
        {
          "supplier_sku": "TSHIRT-RED-ONESIZE",
          "mall_state": 1,
          "height": "10",
          "length": "10",
          "width": "10",
          "weight": 200,
          "price_info_list": [
            { "sub_site": "shein-us", "currency": "USD", "base_price": 14.99 }
          ],
          "stock_info_list": [
            { "inventory_num": 20 }
          ]
        }
      ]
    }
  ],
  "source_system": "openapi"
}
```

### Attribute meaning
- `attribute_id: 1001` → **Color**
- `attribute_value_id: 2001` → **Red**

---

## Example 2 — Color + Size

**Product:**  
T-Shirt with sizes **S / M / L** in **Red** and **Blue**

### Structure

SPU: T-Shirt  
├─ SKC: Red  
│  ├─ SKU: Red / S  
│  ├─ SKU: Red / M  
│  └─ SKU: Red / L  
└─ SKC: Blue  
   ├─ SKU: Blue / S  
   ├─ SKU: Blue / M  
   └─ SKU: Blue / L  

### SKU-level attributes
Size is a `sale_attribute_list` entry on the SKU.

```json
"sale_attribute_list": [
  { "attribute_id": 1002, "attribute_value_id": 3001 }
]
```

### Attribute meaning
- `attribute_id: 1002` → **Size**
- `3001=S`, `3002=M`, `3003=L`

### Example payload (two SKCs, multiple SKUs)

```json
{
  "category_id": 20000000,
  "site_list": [
    { "main_site": "shein", "sub_site_list": ["shein-us"] }
  ],
  "multi_language_name_list": [
    { "language": "en", "name": "Basic T-Shirt" }
  ],
  "multi_language_desc_list": [
    { "language": "en", "name": "T-shirt available in multiple colors and sizes." }
  ],
  "skc_list": [
    {
      "supplier_code": "TSHIRT-RED",
      "sale_attribute": { "attribute_id": 1001, "attribute_value_id": 2001 },
      "image_info": { "image_info_list": [{ "image_sort": 1, "image_type": 1, "image_url": "https://img.shein.com/red_square.jpg" }] },
      "sku_list": [
        {
          "supplier_sku": "TSHIRT-RED-S",
          "mall_state": 1,
          "height": "10", "length": "10", "width": "10", "weight": 200,
          "sale_attribute_list": [{ "attribute_id": 1002, "attribute_value_id": 3001 }],
          "price_info_list": [{ "sub_site": "shein-us", "currency": "USD", "base_price": 14.99 }],
          "stock_info_list": [{ "inventory_num": 10 }]
        },
        {
          "supplier_sku": "TSHIRT-RED-M",
          "mall_state": 1,
          "height": "10", "length": "10", "width": "10", "weight": 210,
          "sale_attribute_list": [{ "attribute_id": 1002, "attribute_value_id": 3002 }],
          "price_info_list": [{ "sub_site": "shein-us", "currency": "USD", "base_price": 14.99 }],
          "stock_info_list": [{ "inventory_num": 12 }]
        },
        {
          "supplier_sku": "TSHIRT-RED-L",
          "mall_state": 1,
          "height": "10", "length": "10", "width": "10", "weight": 220,
          "sale_attribute_list": [{ "attribute_id": 1002, "attribute_value_id": 3003 }],
          "price_info_list": [{ "sub_site": "shein-us", "currency": "USD", "base_price": 14.99 }],
          "stock_info_list": [{ "inventory_num": 8 }]
        }
      ]
    },
    {
      "supplier_code": "TSHIRT-BLUE",
      "sale_attribute": { "attribute_id": 1001, "attribute_value_id": 2002 },
      "image_info": { "image_info_list": [{ "image_sort": 1, "image_type": 1, "image_url": "https://img.shein.com/blue_square.jpg" }] },
      "sku_list": [
        {
          "supplier_sku": "TSHIRT-BLUE-S",
          "mall_state": 1,
          "height": "10", "length": "10", "width": "10", "weight": 200,
          "sale_attribute_list": [{ "attribute_id": 1002, "attribute_value_id": 3001 }],
          "price_info_list": [{ "sub_site": "shein-us", "currency": "USD", "base_price": 14.99 }],
          "stock_info_list": [{ "inventory_num": 11 }]
        },
        {
          "supplier_sku": "TSHIRT-BLUE-M",
          "mall_state": 1,
          "height": "10", "length": "10", "width": "10", "weight": 210,
          "sale_attribute_list": [{ "attribute_id": 1002, "attribute_value_id": 3002 }],
          "price_info_list": [{ "sub_site": "shein-us", "currency": "USD", "base_price": 14.99 }],
          "stock_info_list": [{ "inventory_num": 13 }]
        },
        {
          "supplier_sku": "TSHIRT-BLUE-L",
          "mall_state": 1,
          "height": "10", "length": "10", "width": "10", "weight": 220,
          "sale_attribute_list": [{ "attribute_id": 1002, "attribute_value_id": 3003 }],
          "price_info_list": [{ "sub_site": "shein-us", "currency": "USD", "base_price": 14.99 }],
          "stock_info_list": [{ "inventory_num": 9 }]
        }
      ]
    }
  ],
  "source_system": "openapi"
}
```

**Attribute meaning for colors**
- `attribute_id: 1001` → **Color**
- `2001=Red`, `2002=Blue`

---

## Example 3 — Color + Size + Pack Quantity (IMPORTANT)

This example explains **“200 SKUs per SKC”**.

**Product:**  
Red T-Shirt sold as:
- 1-Pack
- 3-Pack
- 6-Pack  
in sizes S / M / L

### Structure

SPU: T-Shirt  
└─ SKC: Red  
   ├─ SKU: Red / S / 1-Pack  
   ├─ SKU: Red / S / 3-Pack  
   ├─ SKU: Red / S / 6-Pack  
   ├─ SKU: Red / M / 1-Pack  
   ├─ SKU: Red / M / 3-Pack  
   ├─ SKU: Red / M / 6-Pack  
   ├─ SKU: Red / L / 1-Pack  
   ├─ SKU: Red / L / 3-Pack  
   └─ SKU: Red / L / 6-Pack  

### Why this matters
- 3 sizes × 3 pack options = **9 SKUs**
- Add more sizes / packs / fits → can reach **200 SKUs**
- Still ONE SKC (Red)

---

### Preferred way: `quantity_info`

Used when `filled_quantity_to_sku = true` and release specs allow `quantity_info`.

Internal properties used by the integration:
- `quantity_info__unit` (SELECT): 1 = Piece, 2 = Pair
- `quantity_info__quantity` (INTEGER): quantity value used to derive `quantity_type`

Example SKU: **Red / S / 3-Pack**

```json
{
  "supplier_sku": "TSHIRT-RED-S-3P",
  "mall_state": 1,
  "height": "10",
  "length": "10",
  "width": "10",
  "weight": 250,
  "sale_attribute_list": [
    { "attribute_id": 1002, "attribute_value_id": 3001 }
  ],
  "quantity_info": {
    "quantity_type": 2,
    "quantity_unit": 1,
    "quantity": 3
  },
  "price_info_list": [
    { "sub_site": "shein-us", "currency": "USD", "base_price": 34.99 }
  ],
  "stock_info_list": [
    { "inventory_num": 6 }
  ]
}
```

#### `quantity_info` meaning
- `quantity_type: 2` → multiple pieces
- `quantity_unit: 1` → piece
- `quantity: 3` → 3-Pack

---

### Alternative (only if `quantity_info` is not allowed)

Pack is modeled as a second sale attribute:

```json
"sale_attribute_list": [
  { "attribute_id": 1002, "attribute_value_id": 3001 },
  { "attribute_id": 1003, "attribute_value_id": 4002 }
]
```

⚠ Up to 2 sale attributes at the SKU level (in addition to the SKC-level attribute).

---

## What “200 SKUs per SKC” Means (Final Definition)

Under one main variant (SKC, usually Color),
you may define up to **200 distinct purchasable combinations**
using size, pack quantity, fit, material, etc.

It does NOT mean:
- 200 colors
- 200 independent dimensions

---

## Key Agent Rules (Enforce These)

- Always generate at least:
  - 1 SKC
  - 1 SKU per SKC
- Main spec (Color / Style) → SKC only
- Size / Pack / Fit → SKU only
- Do not exceed:
  - 40 SKCs per SPU
  - 200 SKUs per SKC
- Prefer `quantity_info` over fake attributes for packs
- All SKUs under an SKC share the same image set

---

## One-Sentence Mental Model

SPU = product idea  
SKC = main visual option (usually color)  
SKU = what the customer actually buys
