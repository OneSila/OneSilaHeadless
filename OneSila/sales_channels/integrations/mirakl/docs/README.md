# Mirakl Catalog Manager APIs

{% partial file="/partial-content/product/mcm/rest/seller/openapi-description.md" /%}


## Servers

URL to be replaced by your Mirakl instance URL
```
https://your-instance.mirakl.net
```

## Security

### shop_api_key

Type: apiKey
In: header
Name: Authorization

## Download OpenAPI description

[Mirakl Catalog Manager APIs](https://developer.mirakl.com/_bundle/content/product/mcm/rest/seller/openapi3.yaml)

## Stores

### A01 - Get shop information

 - [GET /api/account](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/stores/a01.md): Call Frequency

Recommended usage: Once per day
Maximum usage: Once per day

### A02 - Update shop information

 - [PUT /api/account](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/stores/a02.md): Description

Depending on the operator's configuration, some fields might not be editable.


Call Frequency

Recommended usage: At each information update
Maximum usage: Once per day

### A21 - Get shop statistics

 - [GET /api/account/statistics](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/stores/a21.md): Call Frequency

Recommended usage: Once per day
Maximum usage: Once per day

### S30 - List shop's documents

 - [GET /api/shops/documents](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/stores/s30.md): Description

You must specify at least one of the following parameters: shop_ids, updated_since


Call Frequency

Recommended usage: At each display of a page that includes documents from a store (for example: during the KYC process)
Maximum usage: At each display of a page that includes documents from a store (for example: during the KYC process)

### S32 - Upload business documents to associate with a shop

 - [POST /api/shops/documents](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/stores/s32.md): Description

Document filenames must be distinct and there can be only one file per document type.Only documents of the following types are supported: csv, doc, docx, gif, html, jpeg, latex, mp4, odp, odc, odg, ods, odt, pdf, png, pps, ppsx, ppt, pptx, quicktime, rtf, text, tiff, xls, xlsx, xml, zipYou can upload a maximum of 50 business documents for each shop. These documents are not order related documents.


Call Frequency

Recommended usage: At each business document upload to a shop
Maximum usage: 50 business documents per call

### S31 - Download documents for one or multiple shops

 - [GET /api/shops/documents/download](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/stores/s31.md): Description

          It is mandatory to specify either the shop_ids or the document_ids.  If a list of document identifiers is specified only these documents are downloaded.          If more than one document id is specified, the documents will be wrapped in a ZIP archive      If only one document id is specified the document will not be zipped            If no document identifiers is specified, all the shop documents will be downloaded.    Use a list of shop document type codes to retrieve specific types from your shop.    In this case, the output of the API will always be a ZIP archive even if there is only one document to retrieve.  When documents are retrieved, they're wrapped into a ZIP archive except when only one document id is specified. The tree structure of this archive is as follow:
documents-timestamp.zip
|__ shop_id/
|   |__ image.png
|   |__ image(1).png
|   |__ foo.txt
Returns a 404 if at least one document id or one document type code is invalid


Call Frequency

Recommended usage: After each S30 call, when you want to download documents from a store
Maximum usage: After each S30 call, when you want to download documents from a store

### S33 - Delete a shop document

 - [DELETE /api/shops/documents/{document_id}](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/stores/s33.md): Call Frequency

Recommended usage: At each document deletion from one store
Maximum usage: At each document deletion from one store

## Platform Settings

### AF01 - List all custom fields

 - [GET /api/additional_fields](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/platform-settings/af01.md): Call Frequency

Recommended usage: Once per day
Maximum usage: Once per day
Localization

This resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### CH11 - List all enabled channels

 - [GET /api/channels](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/platform-settings/ch11.md): Description

Results are sorted by code


Call Frequency

Recommended usage: Once per day
Maximum usage: Once per day
Localization

This resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### CUR01 - List currency codes and labels

 - [GET /api/currencies](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/platform-settings/cur01.md): Description

List currency codes and labels activated on the platform


Call Frequency

Recommended usage: Once per day
Maximum usage: Once per day
Localization

This resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### DO01 - List all document types

 - [GET /api/documents](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/platform-settings/do01.md): Call Frequency

Recommended usage: Once per day
Maximum usage: Once per day
Localization

This resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### L01 - List locale codes and labels

 - [GET /api/locales](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/platform-settings/l01.md): Description

List locale codes and labels from your platform to automate product format exports (API H01, PM01, VL01) from your PIM system


Call Frequency

Recommended usage: Once per day
Maximum usage: Once per day

### PC01 - List platform configurations

 - [GET /api/platform/configuration](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/platform-settings/pc01.md): Description

List platform configurations such as general information, modules and features activated.

Note: This configuration represents modules and major features enabled during platform setup. This differs from the PC02 API which export the platform business settings configurable by the operator in the back office.

### V01 - Health Check endpoint

 - [GET /api/version](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/platform-settings/v01.md): Description

Use this endpoint to check that Mirakl Platform is up.You can ignore the response body that is subject to change, checking the response code is enough.

## Products

### CM11 - Export Source Product Data Sheet status

 - [GET /api/mcm/products/sources/status/export](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/cm11.md): Description

Delta export of the source product data sheet status in JSON format.

Define a cron job in your system that periodically calls this API and sets the previous
request date as the updated_since query parameter.


Call Frequency

Recommended usage: - Differential: every 15 minutes
Maximum usage: - Differential: every 5 minutes - Full: every 4 hours
Read More

More contextError troubleshooting

### H11 - List Catalog categories (parents and children) related to a Catalog category

 - [GET /api/hierarchies](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/h11.md): Call Frequency

Recommended usage: Every hour
Maximum usage: Every hour
Read More

More context

### P41 - Import products to the operator information system

 - [POST /api/products/imports](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/p41.md): Description

Returns the import identifier to track the status of the import


Call Frequency

Recommended usage: Every hour, for each seller
Maximum usage: Every 15 minutes, for each seller

### P51 - Get information about product import statuses

 - [GET /api/products/imports](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/p51.md): Description

If the last_request_date param is not set the api returns all product imports.


Call Frequency

Recommended usage: Every 5 minutes
Maximum usage: Once per minute
Pagination

This resource supports offset pagination (see documentation)

Sort fields

sort field can have the following values:dateCreated (Default) - Sort by creation date (asc by default)

### P42 - Get the import status for a product import

 - [GET /api/products/imports/{import}](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/p42.md): Call Frequency

Recommended usage: Once per minute until getting the import final status
Maximum usage: Once per minute
Read More

More context

### P44 - Get the error report file for a product import ("Non-integrated products report")

 - [GET /api/products/imports/{import}/error_report](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/p44.md): Description

This API returns either a CSV file (MCM enabled) or a file in a format defined by the operator (MCM disabled).


Call Frequency

Recommended usage: Each time an error report is needed
Maximum usage: Each time an error report is needed

### P45 - Get the product integration report file for a product import ("Added products report")

 - [GET /api/products/imports/{import}/new_product_report](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/p45.md): Description

This API returns either a CSV file (MCM enabled) or a file in a format defined by the operator (MCM disabled).


Call Frequency

Recommended usage: Each time an integration report is needed
Maximum usage: Each time an integration report is needed
Read More

More context

### P46 - Get the transformed file for a product import ("File in operator format")

 - [GET /api/products/imports/{import}/transformed_file](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/p46.md): Description

This API returns a CSV file.


Call Frequency

Recommended usage: Each time a transformed file is available
Maximum usage: Each time a transformed file is available
Read More

More context

### P47 - Get the transformation error report file for a product import ("Source file error report")

 - [GET /api/products/imports/{import}/transformation_error_report](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/p47.md): Description

This API returns a CSV, XLSX or XML file, depending on the file format provided by the seller.


Call Frequency

Recommended usage: Each time an error report is needed
Maximum usage: Each time an error report is needed
Read More

More context

### PM11 - Get the product attribute configuration

 - [GET /api/products/attributes](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/pm11.md): Description

Retrieves all attributes for parents and children of the requested hierarchy


Call Frequency

Recommended usage: Every hour
Maximum usage: Every hour
Read More

More context

### VL11 - Get information about operator's value lists

 - [GET /api/values_lists](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/products/vl11.md): Call Frequency

Recommended usage: Every hour
Maximum usage: Every hour
Read More

More context

## Users

### RO02 - List shop roles

 - [GET /api/users/shops/roles](https://developer.mirakl.com/content/product/mcm/rest/seller/openapi3/users/ro02.md): Call Frequency

Recommended usage: On each user role view
Maximum usage: On each user role view
Read More

More context
