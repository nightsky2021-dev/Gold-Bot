"""
Invoice/Receipt generation for orders.

Generates downloadable PDF invoices for completed orders.
"""

import logging
from decimal import Decimal
from datetime import datetime
from io import BytesIO
from pathlib import Path

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

logger = logging.getLogger('trading.invoice')


class InvoiceGenerator:
    """Generate PDF invoices for orders."""
    
    # Try to register Persian fonts if available
    FONT_REGISTERED = False
    
    @classmethod
    def _ensure_fonts(cls):
        """Ensure Persian fonts are registered (optional)."""
        if cls.FONT_REGISTERED:
            return
        
        try:
            # Try to register Persian fonts if available
            # This is optional - if fonts aren't available, we'll use default
            font_path = Path(settings.BASE_DIR) / 'static' / 'fonts'
            if font_path.exists():
                persian_font = font_path / 'NotoSansPersian-Regular.ttf'
                if persian_font.exists():
                    pdfmetrics.registerFont(TTFont('Persian', str(persian_font)))
                    cls.FONT_REGISTERED = True
                    logger.info("Persian font registered successfully")
        except Exception as e:
            logger.warning(f"Could not register Persian fonts: {e}. Using default fonts.")
        
        cls.FONT_REGISTERED = True  # Mark as attempted
    
    @classmethod
    def generate_order_invoice(cls, order) -> BytesIO:
        """
        Generate a PDF invoice for an order.
        
        Args:
            order: Order instance
            
        Returns:
            BytesIO containing the PDF data
        """
        cls._ensure_fonts()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            alignment=TA_RIGHT,
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#444444'),
            alignment=TA_RIGHT,
        )
        
        # Add logo if available (optional)
        try:
            logo_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'logo.png'
            if logo_path.exists():
                logo = Image(str(logo_path), width=50*mm, height=50*mm)
                elements.append(logo)
                elements.append(Spacer(1, 10*mm))
        except Exception as e:
            logger.debug(f"Logo not added: {e}")
        
        # Title
        order_type_text = "فاکتور خرید" if order.order_type == 'BUY' else "فاکتور فروش"
        elements.append(Paragraph(order_type_text, title_style))
        elements.append(Spacer(1, 5*mm))
        
        # Invoice metadata
        invoice_data = [
            ['شماره فاکتور:', f'#{order.id}'],
            ['تاریخ:', order.created_at.strftime('%Y/%m/%d - %H:%M')],
            ['وضعیت:', order.get_status_display()],
        ]
        
        invoice_table = Table(invoice_data, colWidths=[40*mm, 80*mm])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 10*mm))
        
        # Customer information
        elements.append(Paragraph('مشخصات مشتری', heading_style))
        customer_data = [
            ['نام:', order.profile.get_display_name()],
            ['شماره تماس:', order.profile.phone_number or 'N/A'],
        ]
        
        customer_table = Table(customer_data, colWidths=[40*mm, 80*mm])
        customer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 10*mm))
        
        # Order details
        elements.append(Paragraph('جزئیات سفارش', heading_style))
        
        # Get product unit
        from trading.services import OrderService
        product_unit = OrderService.get_product_unit(order.product)
        
        order_details_data = [
            ['ردیف', 'محصول', 'مقدار', 'قیمت واحد', 'مبلغ کل'],
            [
                '1',
                order.product.name,
                f'{order.quantity_grams} {product_unit}',
                f'{order.price_per_gram:,.0f} ریال',
                f'{order.total_amount:,.0f} ریال'
            ]
        ]
        
        order_table = Table(order_details_data, colWidths=[15*mm, 50*mm, 30*mm, 35*mm, 40*mm])
        order_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ]))
        elements.append(order_table)
        elements.append(Spacer(1, 10*mm))
        
        # Total summary
        summary_data = [
            ['مبلغ کل:', f'{order.total_amount:,.0f} ریال'],
        ]
        
        summary_table = Table(summary_data, colWidths=[40*mm, 40*mm])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#4CAF50')),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#4CAF50')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 15*mm))
        
        # Footer note
        footer_text = (
            "این فاکتور به صورت الکترونیکی صادر شده و امضای دیجیتال دارد. "
            "برای هرگونه سوال یا مشکل با پشتیبانی تماس بگیرید."
        )
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#888888'),
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer
        buffer.seek(0)
        return buffer
    
    @classmethod
    def get_invoice_filename(cls, order) -> str:
        """
        Generate a filename for the invoice.
        
        Args:
            order: Order instance
            
        Returns:
            Filename string
        """
        order_type = "buy" if order.order_type == 'BUY' else "sell"
        timestamp = order.created_at.strftime('%Y%m%d_%H%M%S')
        return f"invoice_{order_type}_{order.id}_{timestamp}.pdf"

