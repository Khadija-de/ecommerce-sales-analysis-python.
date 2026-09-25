"""Tests for the rule-based product category analysis."""

import unittest

import pandas as pd

from src.ecommerce_sales_analysis import assign_product_category, build_outputs


class ProductCategoryTests(unittest.TestCase):
    def test_assigns_representative_descriptions(self) -> None:
        examples = {
            "CHRISTMAS TREE ORNAMENT": "Seasonal",
            "REGENCY CAKESTAND 3 TIER": "Kitchen & Dining",
            "VINTAGE METAL SIGN": "Home Decor",
            "POSTAGE": "Non-product Charges",
            "UNCLASSIFIED SAMPLE": "Other",
        }

        for description, expected_category in examples.items():
            with self.subTest(description=description):
                self.assertEqual(assign_product_category(description), expected_category)

    def test_category_revenue_reconciles_to_total_revenue(self) -> None:
        clean_df = pd.DataFrame(
            {
                "InvoiceNo": ["100", "100", "101"],
                "Description": ["BLUE MUG", "CHRISTMAS CARD", "POSTAGE"],
                "Quantity": [2, 3, 1],
                "UnitPrice": [5.0, 2.0, 4.0],
                "CustomerID": ["1", "1", "2"],
                "Country": ["United Kingdom"] * 3,
                "InvoiceDate": pd.to_datetime(
                    ["2011-01-03", "2011-01-03", "2011-01-10"]
                ),
                "Revenue": [10.0, 6.0, 4.0],
                "YearMonth": ["2011-01"] * 3,
                "YearWeek": ["2011-W01", "2011-W01", "2011-W02"],
                "Weekday": ["Monday"] * 3,
            }
        )

        category_summary = build_outputs(clean_df)["product_category_summary"]

        self.assertAlmostEqual(category_summary["Revenue"].sum(), 20.0)
        self.assertAlmostEqual(category_summary["RevenueShare"].sum(), 1.0)


if __name__ == "__main__":
    unittest.main()
