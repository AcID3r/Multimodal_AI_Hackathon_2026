"""Export the technical report into a bounded five-section PDF.
Requires optional reportlab and pypdf. Run python -m scripts.build_technical_report.
"""
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from pypdf import PdfReader
from backend.config import ROOT


def build():
    source = (ROOT / "docs/TECHNICAL_REPORT.md").read_text(encoding="utf-8")
    sections = re.split(r"\n## ", source)[1:]
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportBody", fontName="Helvetica", fontSize=9.5,
                              leading=14, spaceAfter=11, textColor=colors.HexColor('#253047')))
    styles.add(ParagraphStyle(name="ReportTitle", fontName="Helvetica-Bold", fontSize=18,
                              leading=23, spaceAfter=18, textColor=colors.HexColor('#17283e')))
    story = []
    for index, section in enumerate(sections):
        if index:
            story.append(PageBreak())
        title, content = section.split('\n', 1)
        story.append(Paragraph('CADENCE / TECHNICAL REPORT', styles['Heading3']))
        story.append(Paragraph(escape(title), styles['ReportTitle']))
        for paragraph in content.strip().split('\n\n'):
            paragraph = escape(paragraph).replace('**', '')
            story.append(Paragraph(paragraph, styles['ReportBody']))
    def footer(canvas, document):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#65718a'))
        canvas.drawString(1.8*cm, 1.1*cm, 'Track C - implementation 1.0.0 - 12 October 2026')
        canvas.drawRightString(A4[0]-1.8*cm, 1.1*cm, str(document.page))
    dest = ROOT / 'docs/TECHNICAL_REPORT.pdf'
    document = SimpleDocTemplate(str(dest), pagesize=A4, topMargin=1.7*cm, bottomMargin=1.7*cm,
                                 leftMargin=1.8*cm, rightMargin=1.8*cm)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    count = len(PdfReader(str(dest)).pages)
    if count > 6:
        raise ValueError(f'Report has {count} pages; competition limit is six')
    print(f'Generated technical report: {count} pages, {dest}')


if __name__ == '__main__':
    build()
