"""
qr_service.py

Generates QR codes that encode a product's Firestore document ID.
Scanning the code (via the browser's camera, see qr-scanner.js on the
frontend) reads that ID back out, and the frontend then either opens
the product's detail view or lets the vendor bump stock up/down --
no backend involvement needed for the *decode* step, since QR decoding
happens entirely in the browser via the html5-qrcode library.

This service's only job is *generating* the image, as a base64 PNG
data URL so it can be embedded directly in JSON responses and <img>
tags without needing file storage (we're intentionally not using
Firebase Storage -- see PHASE2_SETUP.md).
"""

import base64
import io
import qrcode


def generate_qr_code_data_url(product_id):
    """Generate a QR code PNG encoding the product ID, returned as a
    base64 data URL ready to drop into an <img src="..."> tag."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    # Encode a small JSON-free payload: just "product:<id>" so the
    # scanner can distinguish this app's QR codes from arbitrary ones.
    qr.add_data(f"product:{product_id}")
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0F1E17", back_color="#F7F3EA")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{encoded}"
