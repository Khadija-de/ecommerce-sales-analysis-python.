# SQL Analysis Version

This folder contains SQL queries that answer the same business questions as the Python analysis.

## Assumed Table

The queries assume the raw CSV has been imported into a table named `online_retail` with these columns:

- `InvoiceNo`
- `StockCode`
- `Description`
- `Quantity`
- `InvoiceDate`
- `UnitPrice`
- `CustomerID`
- `Country`

## Cleaning Logic

The SQL version follows the same cleaning rules used in Python:

- remove rows with missing product descriptions
- remove rows with missing customer IDs
- remove cancelled invoices where `InvoiceNo` starts with `C`
- remove zero or negative quantities
- remove zero or negative unit prices
- calculate `Revenue` as `Quantity * UnitPrice`

## File

- `online_retail_analysis.sql` — reusable SQL queries for KPIs, revenue trends, rankings, retention, and data quality checks.
