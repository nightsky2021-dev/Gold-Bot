"""
Invoice/Receipt generation for orders.

Generates downloadable PDF invoices for completed orders with proper Persian text support.
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

# Import libraries for Persian text handling
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    PERSIAN_SUPPORT = True
except ImportError:
    PERSIAN_SUPPORT = False
    logging.warning("arabic-reshaper or python-bidi not installed. Persian text may not display correctly.")

logger = logging.getLogger('trading.invoice')


class InvoiceGenerator:
    """Generate PDF invoices for orders with proper Persian text support."""
    
    # Font registration state
    FONT_REGISTERED = False
    PERSIAN_FONT_NAME = None
    
    @classmethod
    def _prepare_persian_text(cls, text: str) -> str:
        """
        Prepare Persian/Arabic text for PDF rendering.
        
        Args:
            text: Persian text to prepare
            
        Returns:
            Reshaped and reversed text ready for PDF
        """
        if not PERSIAN_SUPPORT or not text:
            return text
        
        try:
            # Reshape Persian text (connects letters properly)
            reshaped_text = reshape(text)
            # Reverse for RTL display
            bidi_text = get_display(reshaped_text)
            # Ensure we return a string (get_display can return str or bytes)
            result: str
            if isinstance(bidi_text, bytes):
                result = bidi_text.decode('utf-8')
            else:
                result = str(bidi_text)
            return result
        except Exception as e:
            logger.warning(f"Error processing Persian text: {e}")
            return text
    
    @classmethod
    def _ensure_fonts(cls):
        """Ensure Persian-compatible fonts are registered."""
        if cls.FONT_REGISTERED:
            return
        
        try:
            # Try multiple font locations in order of preference
            font_paths_to_try = [
                # Custom fonts directory
                Path(settings.BASE_DIR) / 'static' / 'fonts',
                # System fonts (Linux)
                Path('/usr/share/fonts/truetype/dejavu'),
                Path('/usr/share/fonts/truetype'),
                # System fonts (Windows)
                Path('C:/Windows/Fonts'),
            ]
            
            font_files_to_try = [
                'NotoSansArabic-Regular.ttf',
                'NotoSans-Regular.ttf', 
                'DejaVuSans.ttf',
                'Arial.ttf',
                'tahoma.ttf',
            ]
            
            font_registered = False
            for base_path in font_paths_to_try:
                if not base_path.exists():
                    continue
                    
                for font_file in font_files_to_try:
                    font_path = base_path / font_file
                    if font_path.exists():
                        try:
                            pdfmetrics.registerFont(TTFont('PersianFont', str(font_path)))
                            cls.PERSIAN_FONT_NAME = 'PersianFont'
                            font_registered = True
                            logger.info(f"Persian font registered successfully: {font_file}")
                            break
                        except Exception as e:
                            logger.debug(f"Failed to register {font_file}: {e}")
                            continue
                
                if font_registered:
                    break
            
            if not font_registered:
                logger.warning("No Persian font found. Using Helvetica (may not display Persian correctly)")
                cls.PERSIAN_FONT_NAME = 'Helvetica'
                
        except Exception as e:
            logger.error(f"Error in font registration: {e}")
            cls.PERSIAN_FONT_NAME = 'Helvetica'
        
        cls.FONT_REGISTERED = True
    
    @classmethod
    def generate_order_invoice(cls, order) -> BytesIO:
        """
        Generate a PDF invoice for an order with proper Persian text support.
        
        Args:
            order: Order instance
            
        Returns:
            BytesIO containing the PDF data
        """
        cls._ensure_fonts()
        
        # Use registered Persian font or fallback
        font_name = cls.PERSIAN_FONT_NAME or 'Helvetica'
        font_name_bold = font_name  # Most fonts don't have separate bold file
        
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
        
        # Styles with Persian font
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            alignment=TA_RIGHT,
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
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
        order_type_text = cls._prepare_persian_text("فاکتور خرید" if order.order_type == 'BUY' else "فاکتور فروش")
        elements.append(Paragraph(order_type_text, title_style))
        elements.append(Spacer(1, 5*mm))
        
        # Invoice metadata
        invoice_number = order.invoice_number or f"#{order.id}"
        invoice_data = [
            [cls._prepare_persian_text('شماره فاکتور:'), invoice_number],
            [cls._prepare_persian_text('تاریخ:'), order.created_at.strftime('%Y/%m/%d - %H:%M')],
            [cls._prepare_persian_text('وضعیت:'), cls._prepare_persian_text(order.get_status_display())],
        ]
        
        invoice_table = Table(invoice_data, colWidths=[40*mm, 80*mm])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 10*mm))
        
        # Customer information
        elements.append(Paragraph(cls._prepare_persian_text('مشخصات مشتری'), heading_style))
        customer_data = [
            [cls._prepare_persian_text('نام:'), cls._prepare_persian_text(order.profile.get_display_name())],
            [cls._prepare_persian_text('شماره تماس:'), order.profile.phone_number or 'N/A'],
            [cls._prepare_persian_text('کد ملی:'), order.profile.national_code or 'N/A'],
        ]
        
        customer_table = Table(customer_data, colWidths=[40*mm, 80*mm])
        customer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 10*mm))
        
        # Order details
        elements.append(Paragraph(cls._prepare_persian_text('جزئیات سفارش'), heading_style))
        
        # Get product unit
        from trading.services import OrderService
        product_unit = OrderService.get_product_unit(order.product)
        
        order_details_data = [
            [
                cls._prepare_persian_text('ردیف'),
                cls._prepare_persian_text('محصول'),
                cls._prepare_persian_text('مقدار'),
                cls._prepare_persian_text('قیمت واحد'),
                cls._prepare_persian_text('مبلغ کل')
            ],
            [
                '1',
                cls._prepare_persian_text(order.product.name),
                cls._prepare_persian_text(f'{order.quantity_grams} {product_unit}'),
                cls._prepare_persian_text(f'{order.price_per_gram:,.0f} ریال'),
                cls._prepare_persian_text(f'{order.total_amount:,.0f} ریال')
            ]
        ]
        
        order_table = Table(order_details_data, colWidths=[15*mm, 50*mm, 30*mm, 35*mm, 40*mm])
        order_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
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
            [cls._prepare_persian_text('مبلغ کل:'), cls._prepare_persian_text(f'{order.total_amount:,.0f} ریال')],
        ]
        
        summary_table = Table(summary_data, colWidths=[40*mm, 40*mm])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#4CAF50')),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#4CAF50')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 15*mm))
        
        # Footer note
        footer_text = cls._prepare_persian_text(
            "این فاکتور به صورت الکترونیکی صادر شده و امضای دیجیتال دارد. "
            "برای هرگونه سوال یا مشکل با پشتیبانی تماس بگیرید."
        )
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName=font_name,
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
        invoice_number = order.invoice_number or str(order.id)
        # Remove special characters from invoice number for filename
        safe_invoice_number = invoice_number.replace('/', '-').replace('\\', '-')
        return f"invoice_{safe_invoice_number}.pdf"

