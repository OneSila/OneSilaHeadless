# VATRate Integration Guide

## Create Remote VatRate
A post-create signal triggers remote creation when a VatRate instance is first saved.

**Signal:** `create_remote_vat_rate`

## Update Remote VatRate
A post-update signal checks if key fields (e.g., `name`) have been modified; if yes, it emits an update signal for remote synchronization.

**Signal:** `update_remote_vat_rate`
