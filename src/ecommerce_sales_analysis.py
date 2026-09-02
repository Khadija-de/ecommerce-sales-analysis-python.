"""Generate sales analysis outputs for the Online Retail dataset.

The script cleans the raw transaction data, calculates business KPIs, and
exports chart-ready tables plus lightweight SVG figures for the README.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "OnlineRetail.csv"
REPORTS_DIR = ROOT / "reports"
TABLES_DIR = REPORTS_DIR / "tables"
FIGURES_DIR = REPORTS_DIR / "figures"


def money(value: float) -> str:
    """Format a numeric value as British pounds."""

    return f"£{value:,.0f}"


def load_data() -> pd.DataFrame:
    """Load the raw Online Retail CSV."""

    return pd.read_csv(DATA_PATH, encoding="latin1", parse_dates=["InvoiceDate"])


def clean_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows that do not represent normal completed sales."""

    clean_df = raw_df.copy()
    clean_df = clean_df.dropna(subset=["Description", "CustomerID"])
    clean_df = clean_df[clean_df["Quantity"] > 0]
    clean_df = clean_df[clean_df["UnitPrice"] > 0]
    clean_df = clean_df[~clean_df["InvoiceNo"].astype(str).str.startswith("C")]
    clean_df["CustomerID"] = clean_df["CustomerID"].astype(int).astype(str)
    clean_df["Revenue"] = clean_df["Quantity"] * clean_df["UnitPrice"]
    clean_df["YearMonth"] = clean_df["InvoiceDate"].dt.to_period("M").astype(str)
    clean_df["YearWeek"] = clean_df["InvoiceDate"].dt.strftime("%G-W%V")
    clean_df["Weekday"] = clean_df["InvoiceDate"].dt.day_name()
    return clean_df


def build_data_quality_report(
    raw_df: pd.DataFrame, clean_df: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Create data-quality tables for transparent cleaning decisions."""

    total_rows = len(raw_df)
    canceled_invoices = raw_df["InvoiceNo"].astype(str).str.startswith("C")
    missing_description = raw_df["Description"].isna()
    missing_customer = raw_df["CustomerID"].isna()
    non_positive_quantity = raw_df["Quantity"] <= 0
    non_positive_unit_price = raw_df["UnitPrice"] <= 0
    exact_duplicates = raw_df.duplicated()

    quality_summary = pd.DataFrame(
        [
            (
                "Missing product descriptions",
                int(missing_description.sum()),
                missing_description.mean(),
                "Cannot support reliable product-level analysis.",
                "Medium",
            ),
            (
                "Missing customer IDs",
                int(missing_customer.sum()),
                missing_customer.mean(),
                "Cannot support customer-level segmentation or retention analysis.",
                "High",
            ),
            (
                "Cancelled invoices",
                int(canceled_invoices.sum()),
                canceled_invoices.mean(),
                "Represents returns or cancellations, not completed sales.",
                "High",
            ),
            (
                "Zero or negative quantity",
                int(non_positive_quantity.sum()),
                non_positive_quantity.mean(),
                "Would distort revenue and volume metrics for normal sales.",
                "High",
            ),
            (
                "Zero or negative unit price",
                int(non_positive_unit_price.sum()),
                non_positive_unit_price.mean(),
                "Would distort revenue and average order value.",
                "High",
            ),
            (
                "Exact duplicate rows",
                int(exact_duplicates.sum()),
                exact_duplicates.mean(),
                "May double-count transactions if not reviewed.",
                "Medium",
            ),
        ],
        columns=["Check", "AffectedRows", "AffectedRate", "AnalyticalRisk", "Severity"],
    )

    cleaning_steps = [
        ("Raw data", raw_df),
        ("Remove missing product descriptions", raw_df.dropna(subset=["Description"])),
    ]
    cleaning_steps.append(
        (
            "Remove zero or negative quantity",
            cleaning_steps[-1][1][cleaning_steps[-1][1]["Quantity"] > 0],
        )
    )
    cleaning_steps.append(
        (
            "Remove zero or negative unit price",
            cleaning_steps[-1][1][cleaning_steps[-1][1]["UnitPrice"] > 0],
        )
    )
    cleaning_steps.append(
        (
            "Remove missing customer IDs",
            cleaning_steps[-1][1].dropna(subset=["CustomerID"]),
        )
    )
    cleaning_steps.append(
        (
            "Remove cancelled invoices",
            cleaning_steps[-1][1][
                ~cleaning_steps[-1][1]["InvoiceNo"].astype(str).str.startswith("C")
            ],
        )
    )

    funnel_rows = []
    previous_rows = None
    for step, step_df in cleaning_steps:
        rows_remaining = len(step_df)
        rows_removed = 0 if previous_rows is None else previous_rows - rows_remaining
        funnel_rows.append((step, rows_remaining, rows_removed, rows_remaining / total_rows))
        previous_rows = rows_remaining

    cleaning_funnel = pd.DataFrame(
        funnel_rows,
        columns=["Step", "RowsRemaining", "RowsRemoved", "RowsRemainingRate"],
    )

    nulls_by_column = (
        raw_df.isna()
        .sum()
        .rename("MissingValues")
        .reset_index()
        .rename(columns={"index": "Column"})
    )
    nulls_by_column["MissingRate"] = nulls_by_column["MissingValues"] / total_rows

    return {
        "data_quality_summary": quality_summary,
        "cleaning_funnel": cleaning_funnel,
        "nulls_by_column": nulls_by_column,
    }


def build_outputs(clean_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create KPI and ranking tables used in the project."""

    invoice_revenue = clean_df.groupby("InvoiceNo", as_index=False)["Revenue"].sum()
    total_revenue = clean_df["Revenue"].sum()

    kpis = pd.DataFrame(
        [
            ("Total revenue", total_revenue),
            ("Completed transactions", len(clean_df)),
            ("Unique invoices", clean_df["InvoiceNo"].nunique()),
            ("Unique customers", clean_df["CustomerID"].nunique()),
            ("Unique products", clean_df["Description"].nunique()),
            ("Countries", clean_df["Country"].nunique()),
            ("Average order value", invoice_revenue["Revenue"].mean()),
        ],
        columns=["Metric", "Value"],
    )

    monthly_revenue = (
        clean_df.groupby("YearMonth", as_index=False)["Revenue"]
        .sum()
        .sort_values("YearMonth")
    )
    weekly_revenue = (
        clean_df.groupby("YearWeek", as_index=False)["Revenue"]
        .sum()
        .sort_values("YearWeek")
    )

    weekday_revenue = (
        clean_df.groupby("Weekday", as_index=False)["Revenue"]
        .sum()
        .assign(
            WeekdayOrder=lambda df: df["Weekday"].map(
                {
                    "Monday": 1,
                    "Tuesday": 2,
                    "Wednesday": 3,
                    "Thursday": 4,
                    "Friday": 5,
                    "Saturday": 6,
                    "Sunday": 7,
                }
            )
        )
        .sort_values("WeekdayOrder")
        .drop(columns="WeekdayOrder")
    )

    seasonality_summary = pd.DataFrame(
        [
            (
                "Highest revenue month",
                monthly_revenue.loc[monthly_revenue["Revenue"].idxmax(), "YearMonth"],
                monthly_revenue["Revenue"].max(),
            ),
            (
                "Lowest revenue month",
                monthly_revenue.loc[monthly_revenue["Revenue"].idxmin(), "YearMonth"],
                monthly_revenue["Revenue"].min(),
            ),
            (
                "Highest revenue week",
                weekly_revenue.loc[weekly_revenue["Revenue"].idxmax(), "YearWeek"],
                weekly_revenue["Revenue"].max(),
            ),
            (
                "Lowest revenue week",
                weekly_revenue.loc[weekly_revenue["Revenue"].idxmin(), "YearWeek"],
                weekly_revenue["Revenue"].min(),
            ),
            (
                "Highest revenue weekday",
                weekday_revenue.loc[weekday_revenue["Revenue"].idxmax(), "Weekday"],
                weekday_revenue["Revenue"].max(),
            ),
            (
                "Lowest revenue weekday",
                weekday_revenue.loc[weekday_revenue["Revenue"].idxmin(), "Weekday"],
                weekday_revenue["Revenue"].min(),
            ),
        ],
        columns=["Insight", "Period", "Revenue"],
    )

    top_products = (
        clean_df.groupby("Description", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )

    top_countries = (
        clean_df.groupby("Country", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )

    top_customers = (
        clean_df.groupby("CustomerID", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )

    customer_metrics = (
        clean_df.groupby("CustomerID")
        .agg(
            InvoiceCount=("InvoiceNo", "nunique"),
            TotalRevenue=("Revenue", "sum"),
            FirstPurchase=("InvoiceDate", "min"),
            LastPurchase=("InvoiceDate", "max"),
        )
        .reset_index()
    )
    customer_metrics["CustomerType"] = customer_metrics["InvoiceCount"].apply(
        lambda invoice_count: "Repeat customer" if invoice_count > 1 else "One-time customer"
    )

    customer_retention_summary = (
        customer_metrics.groupby("CustomerType")
        .agg(
            Customers=("CustomerID", "nunique"),
            Revenue=("TotalRevenue", "sum"),
            AverageRevenuePerCustomer=("TotalRevenue", "mean"),
            AverageInvoicesPerCustomer=("InvoiceCount", "mean"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    customer_retention_summary["CustomerShare"] = (
        customer_retention_summary["Customers"] / customer_metrics["CustomerID"].nunique()
    )
    customer_retention_summary["RevenueShare"] = (
        customer_retention_summary["Revenue"] / total_revenue
    )

    return {
        "kpis": kpis,
        "monthly_revenue": monthly_revenue,
        "weekly_revenue": weekly_revenue,
        "weekday_revenue": weekday_revenue,
        "seasonality_summary": seasonality_summary,
        "top_products": top_products,
        "top_countries": top_countries,
        "top_customers": top_customers,
        "customer_metrics": customer_metrics,
        "customer_retention_summary": customer_retention_summary,
    }


def save_tables(outputs: dict[str, pd.DataFrame]) -> None:
    """Save all tables as CSV files."""

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(TABLES_DIR / f"{name}.csv", index=False)


def svg_bar_chart(
    table: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
    output_path: Path,
    width: int = 900,
    row_height: int = 34,
) -> None:
    """Write a simple horizontal bar chart as SVG."""

    chart = table.copy()
    max_value = chart[value_col].max()
    left = 260
    right = 40
    top = 70
    bar_height = 20
    height = top + len(chart) * row_height + 45
    chart_width = width - left - right

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;fill:#1f2937}.title{font-size:22px;font-weight:700}.label{font-size:13px}.value{font-size:12px;fill:#374151}</style>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text class="title" x="24" y="34">{escape(title)}</text>',
    ]

    for index, row in enumerate(chart.itertuples(index=False), start=0):
        label = str(getattr(row, label_col))
        value = float(getattr(row, value_col))
        y = top + index * row_height
        bar_width = 0 if max_value == 0 else (value / max_value) * chart_width
        label_text = label if len(label) <= 34 else f"{label[:31]}..."
        lines.extend(
            [
                f'<text class="label" x="24" y="{y + 15}">{escape(label_text)}</text>',
                f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="{bar_height}" fill="#3b82f6" rx="4"/>',
                f'<text class="value" x="{left + bar_width + 8:.1f}" y="{y + 15}">{money(value)}</text>',
            ]
        )

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def svg_line_chart(
    table: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
    output_path: Path,
    width: int = 900,
    height: int = 420,
) -> None:
    """Write a simple line chart as SVG."""

    values = table[value_col].astype(float).tolist()
    labels = table[label_col].astype(str).tolist()
    max_value = max(values)
    min_value = min(values)
    left = 70
    right = 40
    top = 70
    bottom = 80
    plot_width = width - left - right
    plot_height = height - top - bottom

    def point(index: int, value: float) -> tuple[float, float]:
        x = left + index * plot_width / max(len(values) - 1, 1)
        scale = (value - min_value) / max(max_value - min_value, 1)
        y = top + plot_height - scale * plot_height
        return x, y

    points = [point(index, value) for index, value in enumerate(values)]
    path_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;fill:#1f2937}.title{font-size:22px;font-weight:700}.axis{font-size:12px;fill:#4b5563}.value{font-size:12px;fill:#374151}</style>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text class="title" x="24" y="34">{escape(title)}</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}" stroke="#d1d5db"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#d1d5db"/>',
        f'<polyline fill="none" stroke="#2563eb" stroke-width="3" points="{path_points}"/>',
    ]

    for index, (x, y) in enumerate(points):
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#1d4ed8"/>')
        if index in {0, len(points) - 1}:
            lines.append(
                f'<text class="value" x="{x - 20:.1f}" y="{y - 10:.1f}">{money(values[index])}</text>'
            )

    for index, label in enumerate(labels):
        if index % 2 == 0 or index == len(labels) - 1:
            x, _ = points[index]
            lines.append(
                f'<text class="axis" x="{x - 22:.1f}" y="{height - 42}" transform="rotate(45 {x - 22:.1f},{height - 42})">{escape(label)}</text>'
            )

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_figures(outputs: dict[str, pd.DataFrame]) -> None:
    """Save chart figures as SVG files."""

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    svg_line_chart(
        outputs["monthly_revenue"],
        "YearMonth",
        "Revenue",
        "Monthly Revenue Trend",
        FIGURES_DIR / "monthly-revenue.svg",
    )
    svg_line_chart(
        outputs["weekly_revenue"],
        "YearWeek",
        "Revenue",
        "Weekly Revenue Trend",
        FIGURES_DIR / "weekly-revenue.svg",
    )
    svg_bar_chart(
        outputs["weekday_revenue"],
        "Weekday",
        "Revenue",
        "Revenue by Weekday",
        FIGURES_DIR / "weekday-revenue.svg",
    )
    svg_bar_chart(
        outputs["top_products"],
        "Description",
        "Revenue",
        "Top 10 Products by Revenue",
        FIGURES_DIR / "top-products.svg",
    )
    svg_bar_chart(
        outputs["top_countries"],
        "Country",
        "Revenue",
        "Top 10 Countries by Revenue",
        FIGURES_DIR / "top-countries.svg",
    )
    svg_bar_chart(
        outputs["customer_retention_summary"],
        "CustomerType",
        "Revenue",
        "Revenue by Customer Retention Type",
        FIGURES_DIR / "customer-retention.svg",
    )


def save_summary(
    clean_df: pd.DataFrame,
    outputs: dict[str, pd.DataFrame],
    quality_outputs: dict[str, pd.DataFrame],
) -> None:
    """Write a short Markdown summary for the portfolio repository."""

    kpi_values = dict(zip(outputs["kpis"]["Metric"], outputs["kpis"]["Value"], strict=True))
    top_product = outputs["top_products"].iloc[0]
    top_country = outputs["top_countries"].iloc[0]
    top_month = outputs["monthly_revenue"].sort_values("Revenue", ascending=False).iloc[0]
    seasonality = outputs["seasonality_summary"].set_index("Insight")
    repeat_customers = outputs["customer_retention_summary"].set_index("CustomerType").loc[
        "Repeat customer"
    ]
    start_date = clean_df["InvoiceDate"].min().date()
    end_date = clean_df["InvoiceDate"].max().date()
    cleaning_funnel = quality_outputs["cleaning_funnel"]
    raw_rows = int(cleaning_funnel.iloc[0]["RowsRemaining"])
    final_rows = int(cleaning_funnel.iloc[-1]["RowsRemaining"])
    removed_rows = raw_rows - final_rows
    removed_rate = removed_rows / raw_rows

    summary = f"""# E-commerce Sales Analysis Summary

## Dataset Scope

- Cleaned sales period: {start_date} to {end_date}
- Completed transactions analyzed: {int(kpi_values["Completed transactions"]):,}
- Unique invoices: {int(kpi_values["Unique invoices"]):,}
- Unique customers: {int(kpi_values["Unique customers"]):,}
- Countries represented: {int(kpi_values["Countries"]):,}
- Raw rows reviewed: {raw_rows:,}
- Rows retained after cleaning: {final_rows:,}
- Rows removed during cleaning: {removed_rows:,} ({removed_rate:.1%})

## Key Results

- Total revenue after cleaning: {money(kpi_values["Total revenue"])}
- Average order value: {money(kpi_values["Average order value"])}
- Highest revenue month: {top_month["YearMonth"]} with {money(top_month["Revenue"])}
- Top revenue product: {top_product["Description"]} with {money(top_product["Revenue"])}
- Top country: {top_country["Country"]} with {money(top_country["Revenue"])}
- Repeat customers generate {repeat_customers["RevenueShare"]:.1%} of cleaned revenue.

## Data Quality Notes

- Missing customer IDs are excluded from the main analysis because customer-level retention and segmentation require a known customer.
- Cancelled invoices and non-positive quantity or price rows are excluded so revenue reflects completed sales.
- Detailed data-quality checks are available in `reports/tables/data_quality_summary.csv`.

## Seasonality Notes

- Strongest sales month: {seasonality.loc["Highest revenue month", "Period"]} with {money(seasonality.loc["Highest revenue month", "Revenue"])}
- Weakest sales month: {seasonality.loc["Lowest revenue month", "Period"]} with {money(seasonality.loc["Lowest revenue month", "Revenue"])}
- Strongest weekday: {seasonality.loc["Highest revenue weekday", "Period"]} with {money(seasonality.loc["Highest revenue weekday", "Revenue"])}
- Weakest weekday: {seasonality.loc["Lowest revenue weekday", "Period"]} with {money(seasonality.loc["Lowest revenue weekday", "Revenue"])}

## Business Recommendations

- Prioritize inventory planning around the highest-revenue products before seasonal peaks.
- Treat the United Kingdom as the core market and investigate growth opportunities in the next highest-revenue countries.
- Use high-value customer segments for retention campaigns, loyalty offers, or targeted communication.
- Protect repeat-customer relationships because they generate most of the cleaned revenue.
- Plan inventory and promotions before the strongest monthly and weekly sales periods.
"""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "summary.md").write_text(summary, encoding="utf-8")


def main() -> None:
    raw_df = load_data()
    clean_df = clean_data(raw_df)
    outputs = build_outputs(clean_df)
    quality_outputs = build_data_quality_report(raw_df, clean_df)
    outputs.update(quality_outputs)
    save_tables(outputs)
    save_figures(outputs)
    save_summary(clean_df, outputs, quality_outputs)
    print("Analysis outputs generated in reports/.")


if __name__ == "__main__":
    main()
