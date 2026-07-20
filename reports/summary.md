# E-commerce Sales Analysis Summary

## Dataset Scope

- Cleaned sales period: 2010-12-01 to 2011-12-09
- Completed transactions analyzed: 397,884
- Unique invoices: 18,532
- Unique customers: 4,338
- Countries represented: 37
- Raw rows reviewed: 541,909
- Rows retained after cleaning: 397,884
- Rows removed during cleaning: 144,025 (26.6%)

## Key Results

- Total revenue after cleaning: £8,911,408
- Average order value: £481
- Highest revenue month: 2011-11 with £1,161,817
- Top revenue product: PAPER CRAFT , LITTLE BIRDIE with £168,470
- Top country: United Kingdom with £7,308,392

## Data Quality Notes

- Missing customer IDs are excluded from the main analysis because customer-level retention and segmentation require a known customer.
- Cancelled invoices and non-positive quantity or price rows are excluded so revenue reflects completed sales.
- Detailed data-quality checks are available in `reports/tables/data_quality_summary.csv`.

## Business Recommendations

- Prioritize inventory planning around the highest-revenue products before seasonal peaks.
- Treat the United Kingdom as the core market and investigate growth opportunities in the next highest-revenue countries.
- Use high-value customer segments for retention campaigns, loyalty offers, or targeted communication.
