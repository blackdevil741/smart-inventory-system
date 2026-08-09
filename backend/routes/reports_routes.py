"""
reports_routes.py

Report generation + download endpoints:
  GET /api/reports/<report_type>?format=pdf|csv

  report_type: inventory | stock_value | low_stock
  format: pdf (default) or csv

Returns the file as a direct download (Content-Disposition: attachment)
so the frontend can trigger it with a simple link/fetch + blob download.
"""

from flask import Blueprint, request, Response
from utils.auth_middleware import require_auth
from utils.responses import error_response
from services.report_service import generate_csv, generate_pdf, REPORT_BUILDERS

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/api/reports/<report_type>", methods=["GET"])
@require_auth
def download_report(report_type):
    if report_type not in REPORT_BUILDERS:
        return error_response(
            f"Unknown report type '{report_type}'. Valid options: {', '.join(REPORT_BUILDERS.keys())}.",
            status_code=400,
        )

    fmt = request.args.get("format", "pdf").lower()

    try:
        if fmt == "csv":
            filename, content = generate_csv(report_type)
            mimetype = "text/csv"
        elif fmt == "pdf":
            filename, content = generate_pdf(report_type)
            mimetype = "application/pdf"
        else:
            return error_response("'format' must be 'pdf' or 'csv'.", status_code=400)
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Couldn't generate report: {str(exc)}", status_code=500)

    return Response(
        content,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
