/*
E-commerce Sales Analysis - SQL Version

Purpose:
Answer the same business questions as the Python analysis using SQL.

Assumption:
The Online Retail CSV has been imported into a table named online_retail.
InvoiceDate should be stored as a timestamp or a date-time compatible text field.
*/

-- 1. Cleaned sales view
-- Keeps only completed sales transactions suitable for revenue analysis.
WITH cleaned_sales AS (
    SELECT
        InvoiceNo,
        StockCode,
        Description,
        Quantity,
        CAST(InvoiceDate AS TIMESTAMP) AS InvoiceDate,
        UnitPrice,
        CAST(CustomerID AS VARCHAR) AS CustomerID,
        Country,
        Quantity * UnitPrice AS Revenue
    FROM online_retail
    WHERE Description IS NOT NULL
      AND CustomerID IS NOT NULL
      AND Quantity > 0
      AND UnitPrice > 0
      AND CAST(InvoiceNo AS VARCHAR) NOT LIKE 'C%'
)
SELECT *
FROM cleaned_sales;


-- 2. Main business KPIs
WITH cleaned_sales AS (
    SELECT
        InvoiceNo,
        Description,
        Quantity,
        UnitPrice,
        CAST(CustomerID AS VARCHAR) AS CustomerID,
        Country,
        Quantity * UnitPrice AS Revenue
    FROM online_retail
    WHERE Description IS NOT NULL
      AND CustomerID IS NOT NULL
      AND Quantity > 0
      AND UnitPrice > 0
      AND CAST(InvoiceNo AS VARCHAR) NOT LIKE 'C%'
),
invoice_revenue AS (
    SELECT
        InvoiceNo,
        SUM(Revenue) AS InvoiceRevenue
    FROM cleaned_sales
    GROUP BY InvoiceNo
)
SELECT
    (SELECT SUM(Revenue) FROM cleaned_sales) AS TotalRevenue,
    (SELECT COUNT(*) FROM cleaned_sales) AS CompletedTransactions,
    (SELECT COUNT(DISTINCT InvoiceNo) FROM cleaned_sales) AS UniqueInvoices,
    (SELECT COUNT(DISTINCT CustomerID) FROM cleaned_sales) AS UniqueCustomers,
    (SELECT COUNT(DISTINCT Description) FROM cleaned_sales) AS UniqueProducts,
    (SELECT COUNT(DISTINCT Country) FROM cleaned_sales) AS Countries,
    (SELECT AVG(InvoiceRevenue) FROM invoice_revenue) AS AverageOrderValue;


-- 3. Monthly revenue trend
WITH cleaned_sales AS (
    SELECT
        CAST(InvoiceDate AS TIMESTAMP) AS InvoiceDate,
        Quantity * UnitPrice AS Revenue
    FROM online_retail
    WHERE Description IS NOT NULL
      AND CustomerID IS NOT NULL
      AND Quantity > 0
      AND UnitPrice > 0
      AND CAST(InvoiceNo AS VARCHAR) NOT LIKE 'C%'
)
SELECT
    DATE_TRUNC('month', InvoiceDate) AS SalesMonth,
    SUM(Revenue) AS Revenue
FROM cleaned_sales
GROUP BY SalesMonth
ORDER BY SalesMonth;


-- 4. Weekly revenue trend
WITH cleaned_sales AS (
    SELECT
        CAST(InvoiceDate AS TIMESTAMP) AS InvoiceDate,
        Quantity * UnitPrice AS Revenue
    FROM online_retail
    WHERE Description IS NOT NULL
      AND CustomerID IS NOT NULL
      AND Quantity > 0
      AND UnitPrice > 0
      AND CAST(InvoiceNo AS VARCHAR) NOT LIKE 'C%'
)
SELECT
    DATE_TRUNC('week', InvoiceDate) AS SalesWeek,
    SUM(Revenue) AS Revenue
FROM cleaned_sales
GROUP BY SalesWeek
ORDER BY SalesWeek;


-- 5. Top 10 products by revenue
WITH cleaned_sales AS (
    SELECT
        Description,
        Quantity * UnitPrice AS Revenue
    FROM online_retail
    WHERE Description IS NOT NULL
      AND CustomerID IS NOT NULL
      AND Quantity > 0
      AND UnitPrice > 0
      AND CAST(InvoiceNo AS VARCHAR) NOT LIKE 'C%'
)
SELECT
    Description,
    SUM(Revenue) AS Revenue
FROM cleaned_sales
GROUP BY Description
ORDER BY Revenue DESC
LIMIT 10;


-- 6. Top 10 countries by revenue
WITH cleaned_sales AS (
    SELECT
        Country,
        Quantity * UnitPrice AS Revenue
    FROM online_retail
    WHERE Description IS NOT NULL
      AND CustomerID IS NOT NULL
      AND Quantity > 0
      AND UnitPrice > 0
      AND CAST(InvoiceNo AS VARCHAR) NOT LIKE 'C%'
)
SELECT
    Country,
    SUM(Revenue) AS Revenue
FROM cleaned_sales
GROUP BY Country
ORDER BY Revenue DESC
LIMIT 10;


-- 7. Top 10 customers by revenue
WITH cleaned_sales AS (
    SELECT
        CAST(CustomerID AS VARCHAR) AS CustomerID,
        Quantity * UnitPrice AS Revenue
    FROM online_retail
    WHERE Description IS NOT NULL
      AND CustomerID IS NOT NULL
      AND Quantity > 0
      AND UnitPrice > 0
      AND CAST(InvoiceNo AS VARCHAR) NOT LIKE 'C%'
)
SELECT
    CustomerID,
    SUM(Revenue) AS Revenue
FROM cleaned_sales
GROUP BY CustomerID
ORDER BY Revenue DESC
LIMIT 10;


-- 8. Customer retention: one-time vs repeat customers
WITH cleaned_sales AS (
    SELECT
        InvoiceNo,
        CAST(CustomerID AS VARCHAR) AS CustomerID,
        Quantity * UnitPrice AS Revenue
    FROM online_retail
    WHERE Description IS NOT NULL
      AND CustomerID IS NOT NULL
      AND Quantity > 0
      AND UnitPrice > 0
      AND CAST(InvoiceNo AS VARCHAR) NOT LIKE 'C%'
),
customer_metrics AS (
    SELECT
        CustomerID,
        COUNT(DISTINCT InvoiceNo) AS InvoiceCount,
        SUM(Revenue) AS TotalRevenue
    FROM cleaned_sales
    GROUP BY CustomerID
),
customer_types AS (
    SELECT
        CustomerID,
        InvoiceCount,
        TotalRevenue,
        CASE
            WHEN InvoiceCount > 1 THEN 'Repeat customer'
            ELSE 'One-time customer'
        END AS CustomerType
    FROM customer_metrics
)
SELECT
    CustomerType,
    COUNT(*) AS Customers,
    SUM(TotalRevenue) AS Revenue,
    AVG(TotalRevenue) AS AverageRevenuePerCustomer,
    AVG(InvoiceCount) AS AverageInvoicesPerCustomer
FROM customer_types
GROUP BY CustomerType
ORDER BY Revenue DESC;


-- 9. Data quality checks
SELECT
    COUNT(*) AS RawRows,
    SUM(CASE WHEN Description IS NULL THEN 1 ELSE 0 END) AS MissingProductDescriptions,
    SUM(CASE WHEN CustomerID IS NULL THEN 1 ELSE 0 END) AS MissingCustomerIDs,
    SUM(CASE WHEN Quantity <= 0 THEN 1 ELSE 0 END) AS ZeroOrNegativeQuantityRows,
    SUM(CASE WHEN UnitPrice <= 0 THEN 1 ELSE 0 END) AS ZeroOrNegativeUnitPriceRows,
    SUM(CASE WHEN CAST(InvoiceNo AS VARCHAR) LIKE 'C%' THEN 1 ELSE 0 END) AS CancelledInvoices
FROM online_retail;
