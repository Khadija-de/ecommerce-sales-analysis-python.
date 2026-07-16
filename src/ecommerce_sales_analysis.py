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
    return clean_df


def build_outputs(clean_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create KPI and ranking tables used in the project."""

    invoice_revenue = clean_df.groupby("InvoiceNo", as_index=False)["Revenue"].sum()

    kpis = pd.DataFrame(
        [
            ("Total revenue", clean_df["Revenue"].sum()),
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

    return {
        "kpis": kpis,
        "monthly_revenue": monthly_revenue,
        "top_products": top_products,
        "top_countries": top_countries,
        "top_customers": top_customers,
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


def save_summary(clean_df: pd.DataFrame, outputs: dict[str, pd.DataFrame]) -> None:
    """Write a short Markdown summary for the portfolio repository."""

    kpi_values = dict(zip(outputs["kpis"]["Metric"], outputs["kpis"]["Value"], strict=True))
    top_product = outputs["top_products"].iloc[0]
    top_country = outputs["top_countries"].iloc[0]
    top_month = outputs["monthly_revenue"].sort_values("Revenue", ascending=False).iloc[0]
    start_date = clean_df["InvoiceDate"].min().date()
    end_date = clean_df["InvoiceDate"].max().date()

    summary = f"""# E-commerce Sales Analysis Summary

## Dataset Scope

- Cleaned sales period: {start_date} to {end_date}
- Completed transactions analyzed: {int(kpi_values["Completed transactions"]):,}
- Unique invoices: {int(kpi_values["Unique invoices"]):,}
- Unique customers: {int(kpi_values["Unique customers"]):,}
- Countries represented: {int(kpi_values["Countries"]):,}

## Key Results

- Total revenue after cleaning: {money(kpi_values["Total revenue"])}
- Average order value: {money(kpi_values["Average order value"])}
- Highest revenue month: {top_month["YearMonth"]} with {money(top_month["Revenue"])}
- Top revenue product: {top_product["Description"]} with {money(top_product["Revenue"])}
- Top country: {top_country["Country"]} with {money(top_country["Revenue"])}

## Business Recommendations

- Prioritize inventory planning around the highest-revenue products before seasonal peaks.
- Treat the United Kingdom as the core market and investigate growth opportunities in the next highest-revenue countries.
- Use high-value customer segments for retention campaigns, loyalty offers, or targeted communication.
"""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "summary.md").write_text(summary, encoding="utf-8")


def main() -> None:
    raw_df = load_data()
    clean_df = clean_data(raw_df)
    outputs = build_outputs(clean_df)
    save_tables(outputs)
    save_figures(outputs)
    save_summary(clean_df, outputs)
    print("Analysis outputs generated in reports/.")


if __name__ == "__main__":
    main()
