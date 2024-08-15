# Inventory

## Philosophy

We have a number of products-types, which each have their own take
on what inventory looks like.  Mostly it's stuff you buy.  But Manufacturable
products you actually make, and configurable products hold no stock at all.

Also, it's important that we only assign stock to supplier products and manufacturable
products to ensure transparancy where possible.

## In detail

To follow the phylosophy, Supplier- and Manufacturable products both
have stock directly assigned to them.

Supplier-products are always 'hidden'.  Used for sums of inventory.
But Manufacturable products are directly assinged to websites or to bundles.
Also do we calculate how much "can" be made based on the bill of materials.

ok - so let's split his up:
1. Supplier product = direct stock
2. Simple Product = Sum of supplier product stock, or 99999 if allow_backorder
3. DropShop product = Sum of supplier product stock, or 99999 if allow_backorder
3. Config Product = No stock
4. Bundle Product = Sum of the simple product, dropship product, manufacturable product and bundle product stock
5. Manufacturable = Direct stock + Manufacturable stock.  (Lead times could be a challenge here)

Do we also want access to the inventory per location?
It seems we may need to eg the paperweight.ie example where he has internal and external stock.

How to we need the stock information:
- Actual number physical
- Actual number reserved
- Actual number available
- Lead time for this number (lowest?)

- Number per location
- Lead time per location

## Absolute number inventory.

1. Ensure you can only direct assign inventory to Manufacturable and SupplierInventory
2. Summise the full stocks (meaning, direct inventory + indirect inventory) without caring about the product-types to keep thing simple
3. Bundles.... TODO
4. Configurable is salable - as in any of the children have stock available.


### Testing

- test Simple
- test Dropshipping
- test Manufacturable
- test Nested Manufacturable with simples and manufacturable
- test Bundles
	- with simples
	- with simples and dropship
	- with dropship
	- with simples and manufacturable
	- with dropship and manufacturable
	- with simples, dropship and manufacturable
- test Nested Bundles
	- bundles within bundles
- test Configurable


## Inventory per ShippingAddress

1. The location in this context actually talks about its "ShippingAddress". Not the InventoryLocation.
2. Where does this leave the lead-times?  Should they be set on the ShippingAddress instead of the InventoryLocation?
3. rename InventoryLocation.location to InventoryLocation.shipping_address + adjust help-text
4. Add flag external_location to ensure we can differenciate when shipping orders which need ordering externally and which can be shipped directly.  + Add to help-text



## What about producable stock?

This is part of the manufacturing modules. Inventory is about what you can ship directly.  Not what you can make.
