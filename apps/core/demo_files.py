"""Generate tiny valid uploads without a fixture dependency or external assets."""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from reportlab.pdfgen.canvas import Canvas


def demo_png() -> SimpleUploadedFile:
    """Exercise the real photo validator with a small genuine PNG."""
    stream = BytesIO()
    Image.new("RGB", (16, 16), (25, 90, 130)).save(stream, format="PNG")
    return SimpleUploadedFile(
        "demo-photo.png", stream.getvalue(), content_type="image/png"
    )


def demo_pdf() -> SimpleUploadedFile:
    """Exercise private library validation using a genuine one-page ReportLab PDF."""
    stream = BytesIO()
    canvas = Canvas(stream, invariant=1, pageCompression=0)
    canvas.drawString(72, 750, "Capacity Connect practice workbook")
    canvas.save()
    return SimpleUploadedFile(
        "demo-workbook.pdf", stream.getvalue(), content_type="application/pdf"
    )
