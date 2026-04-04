"""PDF generation service for legal consultation exports."""

import io
import logging
from datetime import UTC, datetime

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


class PDFService:
    """Generate professional PDF documents for legal consultations."""

    BRAND_COLOR = HexColor("#f59e0b")   # amber-500
    DARK_BG = HexColor("#1f2937")
    TEXT_COLOR = HexColor("#111827")
    GRAY = HexColor("#6b7280")
    LIGHT_GRAY = HexColor("#f3f4f6")
    DARK_TEXT = HexColor("#374151")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_consultation_pdf(
        self,
        query: str,
        answer: str,
        citations: list[dict],
        area: str,
        agent_used: str,
        model: str,
        timestamp: str,
        user_name: str | None = None,
        org_name: str | None = None,
    ) -> bytes:
        """Generate a professional PDF for a legal consultation.

        Args:
            query: The legal question posed by the user.
            answer: The AI-generated response.
            citations: List of citation dicts (title, article, document, etc.).
            area: Legal area identifier (e.g. "laboral").
            agent_used: Name of the AI agent that handled the query.
            model: LLM model identifier.
            timestamp: ISO 8601 timestamp string.
            user_name: Optional full name of the consulting user.
            org_name: Optional organisation name.

        Returns:
            PDF content as bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2.5 * cm,
            rightMargin=2.5 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=f"Consulta TukiJuris — {area.replace('_', ' ').title()}",
            author="TukiJuris",
            subject="Consulta juridica — Derecho Peruano",
        )

        styles = self._build_styles()
        story = self._build_story(
            styles=styles,
            query=query,
            answer=answer,
            citations=citations,
            area=area,
            agent_used=agent_used,
            model=model,
            timestamp=timestamp,
            user_name=user_name,
            org_name=org_name,
        )

        doc.build(story)
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # Story builder
    # ------------------------------------------------------------------

    def _build_story(
        self,
        *,
        styles: dict,
        query: str,
        answer: str,
        citations: list[dict],
        area: str,
        agent_used: str,
        model: str,
        timestamp: str,
        user_name: str | None,
        org_name: str | None,
    ) -> list:
        story = []

        # --- Header ---
        story.append(Paragraph("TukiJuris", styles["brand"]))
        story.append(
            Paragraph(
                "Plataforma Juridica Inteligente \u2014 Derecho Peruano",
                styles["subtitle"],
            )
        )
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="100%", thickness=1.5, color=self.BRAND_COLOR))
        story.append(Spacer(1, 0.6 * cm))

        # --- Metadata table ---
        story.extend(self._build_metadata(styles, area, agent_used, model, timestamp, user_name, org_name))
        story.append(Spacer(1, 0.8 * cm))

        # --- Query section ---
        story.append(Paragraph("CONSULTA", styles["section_header"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(self._escape(query), styles["query_text"]))
        story.append(Spacer(1, 0.8 * cm))

        # --- Answer section ---
        story.append(Paragraph("RESPUESTA", styles["section_header"]))
        story.append(Spacer(1, 0.3 * cm))
        for block in answer.split("\n\n"):
            block = block.strip()
            if block:
                story.append(Paragraph(self._escape(block), styles["answer_text"]))
                story.append(Spacer(1, 0.25 * cm))

        # --- Citations ---
        if citations:
            story.append(Spacer(1, 0.5 * cm))
            story.append(Paragraph("CITACIONES Y REFERENCIAS", styles["section_header"]))
            story.append(Spacer(1, 0.3 * cm))
            for i, cite in enumerate(citations, 1):
                title = cite.get("title") or cite.get("document") or "N/A"
                cite_text = f"{i}. {self._escape(title)}"
                if cite.get("article"):
                    cite_text += f" \u2014 {self._escape(str(cite['article']))}"
                story.append(Paragraph(cite_text, styles["citation"]))
                story.append(Spacer(1, 0.1 * cm))

        # --- Legal disclaimer ---
        story.append(Spacer(1, 1.0 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=self.GRAY))
        story.append(Spacer(1, 0.3 * cm))
        story.append(
            Paragraph(
                "AVISO LEGAL: Esta consulta fue generada por inteligencia artificial y "
                "constituye orientacion juridica, no asesoria legal. Las citaciones son "
                "referenciales. Consulte con un abogado colegiado para decisiones legales.",
                styles["disclaimer"],
            )
        )
        story.append(Spacer(1, 0.2 * cm))
        story.append(
            Paragraph(
                f"Generado por TukiJuris (tukijuris.net.pe) \u2014 "
                f"{datetime.now(UTC).strftime('%d/%m/%Y %H:%M UTC')}",
                styles["footer"],
            )
        )

        return story

    def _build_metadata(
        self,
        styles: dict,
        area: str,
        agent_used: str,
        model: str,
        timestamp: str,
        user_name: str | None,
        org_name: str | None,
    ) -> list:
        """Build the metadata table and return as a list of flowables."""
        # Format timestamp for display
        display_ts = timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            display_ts = dt.strftime("%d/%m/%Y %H:%M UTC")
        except (ValueError, AttributeError):
            pass

        rows = [
            ["Fecha:", display_ts],
            ["Area del Derecho:", area.replace("_", " ").title()],
            ["Agente Utilizado:", agent_used],
            ["Modelo IA:", model],
        ]
        if user_name:
            rows.append(["Consultante:", user_name])
        if org_name:
            rows.append(["Organizacion:", org_name])

        table = Table(rows, colWidths=[4 * cm, 12 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), self.GRAY),
                    ("TEXTCOLOR", (1, 0), (1, -1), self.TEXT_COLOR),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return [table]

    # ------------------------------------------------------------------
    # Style factory
    # ------------------------------------------------------------------

    def _build_styles(self) -> dict:
        """Build and return all custom paragraph styles."""
        base = getSampleStyleSheet()

        return {
            "brand": ParagraphStyle(
                "brand",
                parent=base["Title"],
                fontName="Helvetica-Bold",
                fontSize=22,
                textColor=self.BRAND_COLOR,
                alignment=TA_LEFT,
                spaceAfter=2,
            ),
            "subtitle": ParagraphStyle(
                "subtitle",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=9,
                textColor=self.GRAY,
                alignment=TA_LEFT,
                spaceAfter=0,
            ),
            "section_header": ParagraphStyle(
                "section_header",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                textColor=self.BRAND_COLOR,
                alignment=TA_LEFT,
                letterSpacing=1.5,
                spaceAfter=0,
            ),
            "query_text": ParagraphStyle(
                "query_text",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=10.5,
                textColor=self.TEXT_COLOR,
                alignment=TA_JUSTIFY,
                leading=15,
                leftIndent=10,
                rightIndent=10,
                backColor=self.LIGHT_GRAY,
                borderPad=8,
                borderRadius=4,
            ),
            "answer_text": ParagraphStyle(
                "answer_text",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=10,
                textColor=self.DARK_TEXT,
                alignment=TA_JUSTIFY,
                leading=15,
                spaceAfter=0,
            ),
            "citation": ParagraphStyle(
                "citation",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                textColor=self.DARK_TEXT,
                alignment=TA_LEFT,
                leading=13,
                leftIndent=6,
            ),
            "disclaimer": ParagraphStyle(
                "disclaimer",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7.5,
                textColor=self.GRAY,
                alignment=TA_JUSTIFY,
                leading=11,
            ),
            "footer": ParagraphStyle(
                "footer",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=7,
                textColor=self.GRAY,
                alignment=TA_CENTER,
                spaceBefore=4,
            ),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _escape(text: str) -> str:
        """Escape characters that would break ReportLab's XML parser."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


pdf_service = PDFService()
