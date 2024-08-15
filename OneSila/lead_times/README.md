# Lead times - design choices

## What is lead-time?

Lead time is the time it takes between taking an order, and actually shipping it out.
When an item is in stock, it will most likely be hours or days.

But if an item is out of stock - it can be days to weeks.

All of this depends on the speed of goods availability.

## Then what is delivery time?

Delivery time is the time from taking an order to the order being actually delivered.
Or in other words: LeadTime + Shipping time.

## Structure choices

### In stock items


We assign the in stock items on the shipping address which is assigned on the inventory location.
Why?

Inventory locations can 1 location for an addresses, eg external partners shipping for you.
Or users not caring about precision and just assiging many items to one location.

On the other sides, we also support precise locations. That means 1 inventory location can only be assigned
to 1 sku.  These locations can become 100's or 1000's of locations very quickly.  We don't want to have
to set it every time.

That's why we set it on the shipping address.

### Out of stock items

Out of stock items are more complex.  They don't depend on how fast you work. Instead they depend on how fast
your supplier works.

However, some suppliers will also be dependend on their suppliers.  Eg hybrid wholesalers, they have own stock
but also supplier stock / lead times.

We could argue that it needs to be set both on the product and a potential override on the supplier product.
However, this feels a bit layered.  So instead we choose to start by adding it on the supplier product.

This can be reviewed later.
