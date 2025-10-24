# Shein category flow.

### Step 1:

Use
/open-api/goods/query-category-tree

Will return something like:

{
    "code": "0",
    "msg": "OK",
    "info": {
        "data": [
            {
                "category_id": 2028,
                "product_type_id": 0,
                "parent_category_id": 0,
                "category_name": "女士",
                "last_category": false,
                "children": [
                    {
                        "category_id": 2033,
                        "product_type_id": 0,
                        "parent_category_id": 2028,
                        "category_name": "Clothing",
                        "last_category": false,
                        "children": [
                            {
                                "category_id": 1767,
                                "product_type_id": 0,
                                "parent_category_id": 2033,
                                "category_name": "Dresses中文",
                                "last_category": false,
                                "children": [
                                    {
                                        "category_id": 1727,
                                        "product_type_id": 1080,
                                        "parent_category_id": 1767,
                                        "category_name": "Dresses/中文-四级",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 1740,
                                        "product_type_id": 1080,
                                        "parent_category_id": 1767,
                                        "category_name": "长裤",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 1756,
                                        "product_type_id": 165,
                                        "parent_category_id": 1767,
                                        "category_name": "女士首饰套装",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 1757,
                                        "product_type_id": 80,
                                        "parent_category_id": 1767,
                                        "category_name": "耳环",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 1759,
                                        "product_type_id": 79,
                                        "parent_category_id": 1767,
                                        "category_name": "戒指",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 1777,
                                        "product_type_id": 91,
                                        "parent_category_id": 1767,
                                        "category_name": "女士胸针",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 1871,
                                        "product_type_id": 164,
                                        "parent_category_id": 1767,
                                        "category_name": "打底裤",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 1912,
                                        "product_type_id": 75,
                                        "parent_category_id": 1767,
                                        "category_name": "短裤",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 2157,
                                        "product_type_id": 1178,
                                        "parent_category_id": 1767,
                                        "category_name": "男士公文包",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 2209,
                                        "product_type_id": 367,
                                        "parent_category_id": 1767,
                                        "category_name": "Lakensets met kussenslopen",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 2336,
                                        "product_type_id": 1031,
                                        "parent_category_id": 1767,
                                        "category_name": "库尔塔套装",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 2709,
                                        "product_type_id": 571,
                                        "parent_category_id": 1767,
                                        "category_name": "Women Sweatpants",
                                        "last_category": true,
                                        "children": []
                                    },
                                    {
                                        "category_id": 10409,
                                        "product_type_id": 1080,
                                        "parent_category_id": 1767,
                                        "category_name": "非服装分类",
                                        "last_category": true,
                                        "children": []
                                    }
                                ]
                            },
{
                "category_id": 10011520,
                "product_type_id": 0,
                "parent_category_id": 0,
                "category_name": "分类1208",
                "last_category": false,
                "children": [
                    {
                        "category_id": 10011707,
                        "product_type_id": 2147485898,
                        "parent_category_id": 10011520,
                        "category_name": "测试二级分类111",
                        "last_category": true,
                        "children": []
                    },
                    {
                        "category_id": 10011712,
                        "product_type_id": 2147485901,
                        "parent_category_id": 10011520,
                        "category_name": "测试二级分类222",
                        "last_category": true,
                        "children": []
                    },
                    {
                        "category_id": 10011917,
                        "product_type_id": 2147486497,
                        "parent_category_id": 10011520,
                        "category_name": "测试4级分类C4",
                        "last_category": true,
                        "children": []
                    },
                    {
                        "category_id": 10011918,
                        "product_type_id": 2147486498,
                        "parent_category_id": 10011520,
                        "category_name": "测试2级分类2",
                        "last_category": true,
                        "children": []
                    }
                ]
            }
        ],
        "meta": {
            "count": 47,
            "customObj": null
        }
    },
    "bbl": null
}

We create ll the catrgories and we save everything we have atm the fields. We will have SheinCategory for that that will need to be mapped to our ProductPropertiesRule like EbayProductType or the Amazon one. But we save all this fields there.


### Step 2 use the category id to do:
Product release field specifications (including default language)
/open-api/goods/query-publish-fill-in-standard

Description:
Each store has different norms (requirements) for filling in product publishing fields under each category. It is recommended to call this interface before using the product publishing interface. The scope of requirements that can be queried in this interface includes:

1. Default mandatory language (default_language) for product title and description
2. Whether it is mandatory to provide competitor product link and stock proof (reference_product_link and proof_of_stock) when publishing the product
3. Whether it is mandatory to provide sample information (sample_info) when publishing the product
4. Whether it is mandatory to provide the brand (brand_code) when publishing the product
5. Whether it is mandatory to provide the SKC title (skc_title) when publishing the product
6. Supply price currency for semi-managed and fully managed (currency)
7. Whether the product supports images at SKU and SPU levels (picture_config_list)
8. Whether it is mandatory to provide the minimum stock quantity (minimum_stock_quantity) when publishing the product
9. Whether the product supports uploading detailed images (product_detail_picture)
10. Whether the product supports quantity per SKU (quantity_info)

category_id as param

This return something like this:

{
    "code": "0",
    "msg": "OK",
    "info": {
        "fill_in_standard_list": [
            {
                "module": "reference_info",
                "field_key": "reference_product_link",
                "required": false,
                "show": false
            },
            {
                "module": "reference_info",
                "field_key": "proof_of_stock",
                "required": false,
                "show": false // New solution A example "picture_config_list": [ { "field_key": "switch_spu_picture", "is_true": false }, { "field_key": "spu_image_detail_show", "is_true": true }, { "field_key": "spu_image_detail_required", "is_true": false }, { "field_key": "spu_image_detail_single", "is_true": true }, { "field_key": "spu_image_square_show", "is_true": false }, { "field_key": "spu_image_square_required", "is_true": false }, { "field_key": "skc_image_detail_show", "is_true": true }, { "field_key": "skc_image_detail_required", "is_true": true }, { "field_key": "skc_image_detail_single", "is_true": false }, { "field_key": "skc_image_square_show", "is_true": true }, { "field_key": "skc_image_square_required", "is_true": true }, { "field_key": "sku_image_detail_show", "is_true": true }, { "field_key": "sku_image_detail_required", "is_true": false } ------------------------------------------------------------------------------------------------------------------------------------- // New solution B example "picture_config_list": [ { "field_key": "switch_spu_picture", "is_true": false }, { "field_key": "spu_image_detail_show", "is_true": true }, { "field_key": "spu_image_detail_required", "is_true": true }, { "field_key": "spu_image_detail_single", "is_true": false }, { "field_key": "spu_image_square_show", "is_true": true }, { "field_key": "spu_image_square_required", "is_true": true }, { "field_key": "skc_image_detail_show", "is_true": true }, { "field_key": "skc_image_detail_required", "is_true": true }, { "field_key": "skc_image_detail_single", "is_true": true }, { "field_key": "skc_image_square_show", "is_true": false }, { "field_key": "skc_image_square_required", "is_true": false }, { "field_key": "sku_image_detail_show", "is_true": true }, { "field_key": "sku_image_detail_required", "is_true": false } 

            },
            {
                "module": "basic_info",
                "field_key": "skc_title",
                "required": false,
                "show": true
            },
            {
                "module": "supplier_info",
                "field_key": "minimum_stock_quantity",
                "required": false,
                "show": false
            },
            {
                "module": "sales_info",
                "field_key": "shelf_require",
                "required": false,
                "show": false
            },
            {
                "module": "basic_info",
                "field_key": "brand_code",
                "required": true,
                "show": true
            }
        ],
        "default_language": "en",
        "picture_config_list": [],
        "currency": "GBP",
        "support_sale_attribute_sort": null
    },
    "bbl": null,
    "traceId": "19291dc98a3812a8"
}

picture_config_list have this description 

Whether the product category supports uploading images at the SPU level.

field_key
string	No	
Configuration field。This field is more complex to use, please refer to the detailed plan at API supports uploading SPU and SKU level images
https://open.sheincorp.com/documents/system/4d96fc8f-4913-4211-8630-5d81e7fcc010

switch_spu_picture	The SPU queried by the incoming parameter to check whether the new image upload scheme has been used.
This value is always false if there is no incoming SPU parameter.	This field is not relevant in the product release scenario but is relevant in the editing scenario.
spu_image_detail_show	Whether to display the SPU carousel image	SPU carousel images have different upload methods for single/multiple images.l For single images: 1-Main image is required, maximum 1 imagel For multiple images: 1-Main image is required, maximum 1 image; 2-Detail images are required, maximum 10 images
spu_image_detail_required	Whether the SPU carousel image is required
spu_image_detail_single	Whether the SPU carousel image is a single image
spu_image_square_show	Whether to display the SPU square image	SPU square images: only one image is allowed, thus there is no field to specify whether it's single. When required, the "5-square image" must be provided.
spu_image_square_required	Whether the SPU square image is required
skc_image_detail_show	Whether to display the SKC detail image	SKC detail images: The uploading method differs depending on whether it's single or multiple images.

For single images: "1-main image" must be provided, with a maximum of 1 image.
For multiple images: "1-main image" must be provided, with a maximum of 1 image; "2-detail images" must be provided, with a maximum of 10 images.
skc_image_detail_required	Whether the SKC detail image is required
skc_image_detail_single	Whether the SKC detail image is a single image
skc_image_square_show	Whether to display the SKC square image	SKC square images: only one image is allowed, thus there is no field to specify whether it's single. When required, the "5-square image" must be provided.
skc_image_square_required	Whether the SKC square image is required

The picture_config_list will return something like:
 // New solution A example "picture_config_list": [ { "field_key": "switch_spu_picture", "is_true": false }, { "field_key": "spu_image_detail_show", "is_true": true }, { "field_key": "spu_image_detail_required", "is_true": false }, { "field_key": "spu_image_detail_single", "is_true": true }, { "field_key": "spu_image_square_show", "is_true": false }, { "field_key": "spu_image_square_required", "is_true": false }, { "field_key": "skc_image_detail_show", "is_true": true }, { "field_key": "skc_image_detail_required", "is_true": true }, { "field_key": "skc_image_detail_single", "is_true": false }, { "field_key": "skc_image_square_show", "is_true": true }, { "field_key": "skc_image_square_required", "is_true": true }, { "field_key": "sku_image_detail_show", "is_true": true }, { "field_key": "sku_image_detail_required", "is_true": false } ------------------------------------------------------------------------------------------------------------------------------------- // New solution B example "picture_config_list": [ { "field_key": "switch_spu_picture", "is_true": false }, { "field_key": "spu_image_detail_show", "is_true": true }, { "field_key": "spu_image_detail_required", "is_true": true }, { "field_key": "spu_image_detail_single", "is_true": false }, { "field_key": "spu_image_square_show", "is_true": true }, { "field_key": "spu_image_square_required", "is_true": true }, { "field_key": "skc_image_detail_show", "is_true": true }, { "field_key": "skc_image_detail_required", "is_true": true }, { "field_key": "skc_image_detail_single", "is_true": true }, { "field_key": "skc_image_square_show", "is_true": false }, { "field_key": "skc_image_square_required", "is_true": false }, { "field_key": "sku_image_detail_show", "is_true": true }, { "field_key": "sku_image_detail_required", "is_true": false } 


### Step 3 use the:
/open-api/goods/query-attribute-template


params is:
product_type_id_list
int64[]	Yes	
Type id collection, supports up to10 type ids in a single call

WE will do 1 by 1

{
    "code": "0",
    "msg": "OK",
    "info": {
        "data": [
            {
                "product_type_id": 2512,
                "business_mode": 1,
                "attribute_infos": [
                    {
                        "attribute_id": 87,
                        "attribute_name": "尺寸",
                        "attribute_name_en": "Size",
                        "attribute_is_show": 1,
                        "attribute_source": 1,
                        "attribute_label": 0,
                        "attribute_mode": 2,
                        "data_dimension": 1,
                        "attribute_status": 3,
                        "attribute_type": 1,
                        "business_mode": 1,
                        "is_sample": 1,
                        "supplier_id": 0,
                        "attribute_doc": null,
                        "attribute_doc_image_list": null,
                        "attribute_value_info_list": [
                            {
                                "attribute_value_id": 474,
                                "attribute_value": "单一尺寸",
                                "attribute_value_en": "one-size",
                                "is_custom_attribute_value": false,
                                "is_show": 1,
                                "supplier_id": 0,
                                "attribute_value_doc": null,
                                "attribute_value_doc_image_list": null,
                                "attribute_value_group_list": null
                            },
                            {
                                "attribute_value_id": 1448,
                                "attribute_value": "",
                                "attribute_value_en": "",
                                "is_custom_attribute_value": false,
                                "is_show": 1,
                                "supplier_id": 0,
                                "attribute_value_doc": null,
                                "attribute_value_doc_image_list": null,
                                "attribute_value_group_list": null
                            },
                            ...
                        ]
                    },
                    {
                        "attribute_id": 27,
                        "attribute_name": "颜色",
                        "attribute_name_en": "color",
                        "attribute_is_show": 1,
                        "attribute_source": 1,
                        "attribute_label": 1,
                        "attribute_mode": 2,
                        "data_dimension": 1,
                        "attribute_status": 3,
                        "attribute_type": 1,
                        "business_mode": 1,
                        "is_sample": 0,
                        "supplier_id": 0,
                        "attribute_doc": null,
                        "attribute_doc_image_list": null,
                        "attribute_value_info_list": [
                            {
                                "attribute_value_id": 78,
                                "attribute_value": "杏色",
                                "attribute_value_en": "Apricot",
                                "is_custom_attribute_value": false,
                                "is_show": 1,
                                "supplier_id": 0,
                                "attribute_value_doc": null,
                                "attribute_value_doc_image_list": null,
                                "attribute_value_group_list": null
                            },
                            {
                                "attribute_value_id": 81,
                                "attribute_value": "军绿色",
                                "attribute_value_en": "Army Green",
                                "is_custom_attribute_value": false,
                                "is_show": 1,
                                "supplier_id": 0,
                                "attribute_value_doc": null,
                                "attribute_value_doc_image_list": null,
                                "attribute_value_group_list": null
                            },
                            {
                                "attribute_value_id": 103,
                                "attribute_value": "米色",
                                "attribute_value_en": "Beige",
                                "is_custom_attribute_value": false,
                                "is_show": 1,
                                "supplier_id": 0,
                                "attribute_value_doc": null,
                                "attribute_value_doc_image_list": null,
                                "attribute_value_group_list": null
                            },
                            ...
                        ]
                    },
                ],
                "attribute_id": [
                    87,
                    27,
                    109,
                    160,
                    1000547,
                    62,
                    55,
                    118,
                    48,
                    32,
                    1000411,
                    1000463,
                    1000186,
                    1000462,
                    1000407,
                    1000546,
                    1000576,
                    1000062
                ]
            }
        ],
        "meta": {
            "count": 1,
            "customObj": null
        }
    },
    "bbl": null
}

We will create SheinLanguage simple based on this defaults.

And here is the "legend" because I will like to have status instead of numbers 1,2,3 Like readable statuses in enums

attribute_is_show
Will the attribute be displayed on the consumer side; 1-Display, 2-Do not display

attribute_type (very important later)
Attribute type。Determines in which field the attribute will be passed in the product publishing interface。 1- Sales attribute (passed in skc_list and sku_list)；2- Size attribute (passed in size_attribute_list), 3- Composition attribute (passed in product_attribute_list), 4- Common attribute (passed in product_attribute_list)

attribute_label
Main sales attribute (SKC attribute tag)。Only the main sales attribute can be passed in skc_list。 1- represents it is the main sales attribute, the main sales attribute can also be used as a secondary sales attribute; 0: Not the main sales attribute。

attribute_mode (will need to map with our type)
Attribute value input method。 0 - Manual input of attribute value, common for size attributes, only positive integers can be entered, must be passed in attribute_extra_value； 1- Dropdown multi-select, i.e., an attribute can have multiple attribute values, must be passed in attribute_value_id； 2- Sales attribute exclusive, dropdown single-select, must be passed in attribute_value_id； 3- Dropdown single-select, must be passed in attribute_value_id； 4- Dropdown multi-select + manual input of parameters, must be passed in attribute_value_id and attribute_extra_value

attribute_input_num
Attribute value count limit。 When attribute_mode=1, the maximum number of selectable attribute values, 0 represents no limit。

attribute_status
Is the attribute required. 1-Not fillable (the attribute may have been deprecated); 2-Optional; 3-Required. If the required attribute is not filled, an error will occur;

attribute_remark_list
Attribute identification. Indicates which scenario the attribute belongs to. 1:Important, 2:Compliance, 3:Quality, 4:Customs

So based on that we can create the SheinCategoryItem / SheinProperty and with the attribute_value_info_list even the SheinPropertyValue but there is a main key here different from other integration. SheinProperty contain the type and the common things. But the SheinCategoryItem will have things like (attribute_is_show / attribute_type / attribute_label) .. things that are configurable per category.

### Step 4:
Query whether custom attribute values are supported
/open-api/goods/get-custom-attribute-permission-config

Queries whether a certain category can customize the attribute values of sales attributes.

Note: Not all merchants and all categories can customize attribute values. Before creating custom attribute values, be sure to query this interface to determine whether the Y category of merchant X can customize attribute values.

This will fill our already existent "Allow unmaped values"

Parameters:
category_id_list
int64[]	Yes	
Last-level category ID, supports up to 200

Response:
{
    "code": "0",
    "msg": "OK",
    "info": {
        "data": [
            {
                "has_permission": 1,
                "last_category_id": 2103,
                "attribute_id": 27
            },
            {
                "has_permission": 1,
                "last_category_id": 2103,
                "attribute_id": 87
            }
        ],
        "meta": {
            "count": 2,
            "customObj": null
        }
    },
    "bbl": null
}


If the categories have permission for custom values (this also depend on the rule so it will probably be added inside the SheinCategoryItem) then we can add custom values with:

/open-api/goods/add-custom-attribute-value

attribute_id
int64	Yes	
Attribute ID。

Under which attribute to add the custom attribute value。

attribute_value
string	Yes	
Custom attribute value. Up to 100 characters, special symbols must use half-width, full-width symbols are not supported。
category_id
int64	Yes	
Sub-category ID

attribute_value_name_multis
object[]	No	
Multilingual for custom attribute value
language
string	No	
Language

attribute_value_name_multi
string	No	
Custom attribute value (multilingual)。Up to 100 characters, special symbols must use half-width, full-width symbols are not supported。

And we will get a attribute_value_id in return.

# Internal properties

SheinInternalProperty and EbayInternalPropertyOption

brand_code the options are obtained with
/open-api/goods/query-brand-list

规范类型。包含以下枚举值

1、reference_product_link（商品参考链接，对应发布的competing_product_link）
2、sample_spec（样品，对应发布的sample_info）
3、proof_of_stock（库存证明，对应发布的proof_of_stock_list）
4、shelf_require（强制上架，对应发布的shelf_require）
5、brand_code（品牌，对应发布的brand_code）
6、skc_title（skc标题，对应发布的skc_title)
7、minimum_stock_quantity（最小备货量，对应minimum_stock_quantity）
8、product_detail_picture（商品详情图，对应site_detail_image_info_list）
9、quantity_info（是否可传SKU件数，对应filled_quantity_to_sku和quantity_info）

Determined per categhories but we need this tattributes to be mapped.