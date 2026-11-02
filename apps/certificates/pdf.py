"""Render a reproducible one-page formal certificate using built-in fonts."""

from io import BytesIO

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from apps.certificates.constants import GOLD, INK
from apps.certificates.dataclasses import CertificateData

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)


def safe_text(value: str) -> str:
    """Replace unsupported built-in-font characters without interpreting markup."""
    return " ".join(value.encode("cp1252", errors="replace").decode("cp1252").split())


def centered(canvas: Canvas, text: str, y: float, style: tuple) -> None:
    """Fit untrusted names/titles to the certificate's inner width."""
    font, size = style
    text = safe_text(text)
    width = PAGE_WIDTH - 170
    while stringWidth(text, font, size) > width and size > 10:
        size -= 1
    while stringWidth(text, font, size) > width:
        text = text[:-4] + "..."
    canvas.setFont(font, size)
    canvas.drawCentredString(PAGE_WIDTH / 2, y, text)


def borders(canvas: Canvas) -> None:
    """Frame the landscape page with a double outer and inner gold border."""
    canvas.setStrokeColor(HexColor(INK))
    canvas.setLineWidth(2)
    canvas.rect(25, 25, PAGE_WIDTH - 50, PAGE_HEIGHT - 50)
    canvas.setLineWidth(0.6)
    canvas.rect(31, 31, PAGE_WIDTH - 62, PAGE_HEIGHT - 62)
    canvas.setStrokeColor(HexColor(GOLD))
    canvas.setLineWidth(1)
    canvas.rect(43, 43, PAGE_WIDTH - 86, PAGE_HEIGHT - 86)


def roundel(canvas: Canvas) -> None:
    """Draw the metro emblem on the canvas without external assets."""
    x, y = PAGE_WIDTH / 2, 510
    canvas.setStrokeColor(HexColor(GOLD))
    canvas.setLineWidth(6)
    canvas.circle(x, y, 18)
    canvas.setFillColor(HexColor(INK))
    canvas.rect(x - 30, y - 6, 60, 12, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawCentredString(x, y - 2, "CONNECT")
    canvas.setFillColor(HexColor(INK))


def main_text(canvas: Canvas, data: CertificateData) -> None:
    """Keep the certificate's main hierarchy readable and centered."""
    centered(
        canvas, "Capacity Connect · Learning & Development", 466, ("Helvetica", 12)
    )
    centered(canvas, "CERTIFICATE OF COMPLETION", 417, ("Times-Bold", 28))
    centered(canvas, "This is to certify that", 374, ("Times-Roman", 14))
    centered(canvas, data.trainee_name, 331, ("Times-Italic", 32))
    centered(canvas, "has successfully completed", 296, ("Times-Roman", 14))
    centered(canvas, data.course_title, 258, ("Times-Bold", 22))
    centered(
        canvas,
        f"with an average assessment score of {data.average_percent:.2f}% "
        f"· Grade {data.grade}",
        222,
        ("Helvetica", 12),
    )
    canvas.setStrokeColor(HexColor(GOLD))
    canvas.setLineWidth(1)
    canvas.line(210, 194, PAGE_WIDTH - 210, 194)
    for x in (210, PAGE_WIDTH / 2, PAGE_WIDTH - 210):
        canvas.circle(x, 194, 3, fill=1)


def signatures(canvas: Canvas, data: CertificateData) -> None:
    """Separate the trainer and configured signatory with a drawn verified seal."""
    canvas.setStrokeColor(HexColor(INK))
    canvas.setLineWidth(0.6)
    for x, name, title in (
        (230, data.trainer_name, "Lead Trainer"),
        (612, data.signatory_name, data.signatory_title),
    ):
        canvas.line(x - 90, 135, x + 90, 135)
        canvas.setFont("Times-Italic", 12)
        canvas.drawCentredString(x, 145, safe_text(name)[:30])
        canvas.setFont("Helvetica", 9)
        canvas.drawCentredString(x, 119, safe_text(title)[:40])
    canvas.setStrokeColor(HexColor(GOLD))
    canvas.circle(PAGE_WIDTH / 2, 139, 28)
    canvas.circle(PAGE_WIDTH / 2, 139, 24)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawCentredString(PAGE_WIDTH / 2, 137, "VERIFIED")


def footer(canvas: Canvas, data: CertificateData) -> None:
    """Make the stored identifier/date/public lookup available on the printed record."""
    centered(
        canvas,
        f"Certificate {data.certificate_id}  ·  Issued {data.issued_on.isoformat()}",
        80,
        ("Helvetica", 9),
    )
    centered(canvas, data.verification_url, 62, ("Helvetica", 8))


def render_certificate_pdf(data: CertificateData) -> bytes:
    """Produce deterministic bytes without database, clock or storage access."""
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=landscape(A4), invariant=1, pageCompression=0)
    canvas.setTitle("Capacity Connect Certificate of Completion")
    borders(canvas)
    roundel(canvas)
    main_text(canvas, data)
    signatures(canvas, data)
    footer(canvas, data)
    canvas.showPage()
    canvas.save()
    return stream.getvalue()
