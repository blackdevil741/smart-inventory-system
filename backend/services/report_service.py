"""
report_service.py

Generates downloadable reports: Inventory, Stock Value, and Low Stock,
each exportable as PDF (via reportlab) or CSV. Reports are built
entirely in memory (no temp files on disk) and streamed back as a
file download from the route handler.
"""

import csv
import io
from datetime import datetime, timezone

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from firebase_config import db

PRODUCTS_COLLECTION = "products"

# Report definitions: each returns (title, headers, rows) where rows
# is a list of lists matching headers, ready for both CSV and PDF.

def _fetch_products():
    return [{**doc.to_dict(), "id": doc.id} for doc in db.collection(PRODUCTS_COLLECTION).stream()]


def build_inventory_report():
    products = _fetch_products()
    headers = ["Name", "SKU", "Category", "Quantity", "Cost Price", "Selling Price", "Vendor"]
    rows = [
        [p.get("name", ""), p.get("sku", ""), p.get("category", ""), p.get("quantity", 0),
         f"{p.get('cost_price', 0):.2f}", f"{p.get('selling_price', 0):.2f}", p.get("vendor_name", "")]
        for p in sorted(products, key=lambda p: p.get("name", "").lower())
    ]
    return "Inventory Report", headers, rows


def build_stock_value_report():
    products = _fetch_products()
    headers = ["Name", "SKU", "Quantity", "Cost Price", "Cost Value", "Selling Price", "Potential Revenue"]
    rows = []
    for p in sorted(products, key=lambda p: -(p.get("quantity", 0) * p.get("cost_price", 0))):
        qty = p.get("quantity", 0)
        cost = p.get("cost_price", 0)
        sell = p.get("selling_price", 0)
        rows.append([
            p.get("name", ""), p.get("sku", ""), qty,
            f"{cost:.2f}", f"{qty * cost:.2f}", f"{sell:.2f}", f"{qty * sell:.2f}",
        ])
    return "Stock Value Report", headers, rows


def build_low_stock_report():
    products = _fetch_products()
    low_stock = [
        p for p in products
        if p.get("quantity", 0) <= p.get("min_quantity_threshold", 5)
    ]
    headers = ["Name", "SKU", "Category", "Quantity", "Threshold", "Vendor", "Status"]
    rows = []
    for p in sorted(low_stock, key=lambda p: p.get("quantity", 0)):
        status = "OUT OF STOCK" if p.get("quantity", 0) <= 0 else "LOW STOCK"
        rows.append([
            p.get("name", ""), p.get("sku", ""), p.get("category", ""),
            p.get("quantity", 0), p.get("min_quantity_threshold", 5),
            p.get("vendor_name", ""), status,
        ])
    return "Low Stock Report", headers, rows


REPORT_BUILDERS = {
    "inventory": build_inventory_report,
    "stock_value": build_stock_value_report,
    "low_stock": build_low_stock_report,
}


def generate_csv(report_type):
    """Returns (filename, csv_bytes) for the given report type."""
    if report_type not in REPORT_BUILDERS:
        raise ValueError(f"Unknown report type: {report_type}")

    title, headers, rows = REPORT_BUILDERS[report_type]()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)

    filename = f"{report_type}_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return filename, buffer.getvalue().encode("utf-8")


def generate_pdf(report_type):
    """Returns (filename, pdf_bytes) for the given report type."""
    if report_type not in REPORT_BUILDERS:
        raise ValueError(f"Unknown report type: {report_type}")

    title, headers, rows = REPORT_BUILDERS[report_type]()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontSize=18, spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "ReportMeta", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#8A8578"),
    )

    story = [
        Paragraph(title, title_style),
        Paragraph(
            f"Smart Inventory System &middot; Generated {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')} &middot; {len(rows)} item(s)",
            meta_style,
        ),
        Spacer(1, 16),
    ]

    if rows:
        table_data = [headers] + [[str(cell) for cell in row] for row in rows]
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F1E17")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F3EA")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DED8C8")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No items to report.", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)

    filename = f"{report_type}_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    return filename, buffer.getvalue()
