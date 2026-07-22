import io
import html
import pandas as pd
from typing import List, Dict, Any

class ExportService:
    @staticmethod
    def export_to_csv(columns: List[str], rows: List[Dict[str, Any]]) -> io.BytesIO:
        df = pd.DataFrame(rows, columns=columns)
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return output

    @staticmethod
    def export_to_excel(columns: List[str], rows: List[Dict[str, Any]]) -> io.BytesIO:
        df = pd.DataFrame(rows, columns=columns)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Query Results')
        output.seek(0)
        return output

    @staticmethod
    def export_to_pdf(columns: List[str], rows: List[Dict[str, Any]], sql_query: str) -> io.BytesIO:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=12
        )
        story.append(Paragraph("AI Text-to-SQL Query Report", title_style))

        sql_style = ParagraphStyle(
            'SqlStyle',
            parent=styles['Code'],
            fontSize=10,
            textColor=colors.HexColor('#2563EB'),
            backColor=colors.HexColor('#F1F5F9'),
            spaceAfter=14
        )
        escaped_sql = html.escape(sql_query)
        story.append(Paragraph(f"<b>Executed SQL:</b> <br/><code>{escaped_sql}</code>", sql_style))

        # Convert table data safely
        table_data = [[html.escape(str(col)) for col in columns]]
        for row in rows:
            table_data.append([html.escape(str(row.get(col, ''))) for col in columns])

        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ]))
        story.append(t)

        doc.build(story)
        output.seek(0)
        return output

export_service = ExportService()
