"""
Reporting and Export Services for Trading System.

Provides comprehensive reporting functionality including:
- Transaction history export (PDF/CSV)
- Analytics and statistics
- User activity reports
- Business intelligence reports
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
import csv

from django.db.models import Sum, Count, Avg, Q, F, QuerySet
from django.utils import timezone
from django.http import HttpResponse

# PDF generation
try:
    from reportlab.lib import colors  # type: ignore[import-not-found]
    from reportlab.lib.pagesizes import letter, A4  # type: ignore[import-not-found]
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore[import-not-found]
    from reportlab.lib.units import inch  # type: ignore[import-not-found]
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak  # type: ignore[import-not-found]
    from reportlab.pdfgen import canvas  # type: ignore[import-not-found]
    from reportlab.pdfbase import pdfmetrics  # type: ignore[import-not-found]
    from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-not-found]
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from .models import Order, Transaction, Product
from users.models import Profile


class TransactionReportService:
    """Service for generating transaction history reports."""
    
    @staticmethod
    def filter_transactions(
        profile: Profile,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
        product: Optional[Product] = None,
        status: Optional[str] = None
    ) -> QuerySet:
        """
        Filter transactions based on provided criteria.
        
        Args:
            profile: User profile
            start_date: Filter from this date
            end_date: Filter until this date
            transaction_type: Type of transaction (BUY, SELL, DEPOSIT, WITHDRAW)
            product: Specific product filter
            status: Transaction status
            
        Returns:
            Filtered transaction queryset
        """
        transactions = Transaction.objects.filter(profile=profile)
        
        if start_date:
            transactions = transactions.filter(created_at__gte=start_date)
        
        if end_date:
            transactions = transactions.filter(created_at__lte=end_date)
        
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        if status:
            transactions = transactions.filter(status=status)
        
        return transactions.order_by('-created_at')
    
    @staticmethod
    def filter_orders(
        profile: Profile,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_type: Optional[str] = None,
        product: Optional[Product] = None,
        status: Optional[str] = None
    ) -> QuerySet:
        """
        Filter orders based on provided criteria.
        
        Args:
            profile: User profile
            start_date: Filter from this date
            end_date: Filter until this date
            order_type: Type of order (BUY, SELL)
            product: Specific product filter
            status: Order status
            
        Returns:
            Filtered order queryset
        """
        orders = Order.objects.filter(profile=profile)
        
        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        
        if end_date:
            orders = orders.filter(created_at__lte=end_date)
        
        if order_type:
            orders = orders.filter(order_type=order_type)
        
        if product:
            orders = orders.filter(product=product)
        
        if status:
            orders = orders.filter(status=status)
        
        return orders.order_by('-created_at')
    
    @staticmethod
    def get_summary_statistics(
        profile: Profile,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for user transactions.
        
        Args:
            profile: User profile
            start_date: Filter from this date
            end_date: Filter until this date
            
        Returns:
            Dictionary containing summary statistics
        """
        orders = TransactionReportService.filter_orders(
            profile=profile,
            start_date=start_date,
            end_date=end_date,
            status=Order.OrderStatus.COMPLETED
        )
        
        transactions = TransactionReportService.filter_transactions(
            profile=profile,
            start_date=start_date,
            end_date=end_date,
            status=Transaction.TransactionStatus.COMPLETED
        )
        
        # Order statistics
        buy_orders = orders.filter(order_type=Order.OrderType.BUY)
        sell_orders = orders.filter(order_type=Order.OrderType.SELL)
        
        buy_stats = buy_orders.aggregate(
            total_quantity=Sum('quantity_grams'),
            total_amount=Sum('total_amount'),
            count=Count('id'),
            avg_price=Avg('price_per_gram')
        )
        
        sell_stats = sell_orders.aggregate(
            total_quantity=Sum('quantity_grams'),
            total_amount=Sum('total_amount'),
            count=Count('id'),
            avg_price=Avg('price_per_gram')
        )
        
        # Transaction statistics
        deposits = transactions.filter(transaction_type=Transaction.TransactionType.DEPOSIT)
        withdrawals = transactions.filter(transaction_type=Transaction.TransactionType.WITHDRAW)
        
        deposit_stats = deposits.aggregate(
            total_rial=Sum('amount', filter=Q(currency='RIAL')),
            total_gold=Sum('amount', filter=Q(currency='GOLD')),
            count=Count('id')
        )
        
        withdrawal_stats = withdrawals.aggregate(
            total_rial=Sum('amount', filter=Q(currency='RIAL')),
            total_gold=Sum('amount', filter=Q(currency='GOLD')),
            count=Count('id')
        )
        
        return {
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'orders': {
                'buy': {
                    'count': buy_stats['count'] or 0,
                    'total_quantity': float(buy_stats['total_quantity'] or 0),
                    'total_amount': float(buy_stats['total_amount'] or 0),
                    'avg_price': float(buy_stats['avg_price'] or 0)
                },
                'sell': {
                    'count': sell_stats['count'] or 0,
                    'total_quantity': float(sell_stats['total_quantity'] or 0),
                    'total_amount': float(sell_stats['total_amount'] or 0),
                    'avg_price': float(sell_stats['avg_price'] or 0)
                },
                'net': {
                    'quantity': float((buy_stats['total_quantity'] or 0) - (sell_stats['total_quantity'] or 0)),
                    'amount': float((buy_stats['total_amount'] or 0) - (sell_stats['total_amount'] or 0))
                }
            },
            'transactions': {
                'deposits': {
                    'count': deposit_stats['count'] or 0,
                    'total_rial': float(deposit_stats['total_rial'] or 0),
                    'total_gold': float(deposit_stats['total_gold'] or 0)
                },
                'withdrawals': {
                    'count': withdrawal_stats['count'] or 0,
                    'total_rial': float(withdrawal_stats['total_rial'] or 0),
                    'total_gold': float(withdrawal_stats['total_gold'] or 0)
                }
            },
            'current_balance': {
                'rial': float(profile.rial_balance),
                'gold': float(profile.gold_balance_grams),
                'coin': float(profile.coin_balance),
                'dollar': float(profile.dollar_balance)
            }
        }


class CSVExportService:
    """Service for exporting transaction data to CSV format."""
    
    @staticmethod
    def export_transactions_csv(
        profile: Profile,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None
    ) -> HttpResponse:
        """
        Export user transactions to CSV format.
        
        Args:
            profile: User profile
            start_date: Filter from this date
            end_date: Filter until this date
            transaction_type: Type of transaction
            
        Returns:
            HTTP response with CSV file
        """
        transactions = TransactionReportService.filter_transactions(
            profile=profile,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type
        )
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="transactions_{profile.telegram_id}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        # Headers
        writer.writerow([
            'تاریخ',
            'نوع تراکنش',
            'ارز',
            'مقدار',
            'وضعیت',
            'توضیحات'
        ])
        
        # Data rows
        for txn in transactions:
            writer.writerow([
                txn.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                txn.get_transaction_type_display(),
                txn.get_currency_display(),
                f"{txn.amount:,.2f}",
                txn.get_status_display(),
                txn.description or ''
            ])
        
        return response
    
    @staticmethod
    def export_orders_csv(
        profile: Profile,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_type: Optional[str] = None,
        product: Optional[Product] = None
    ) -> HttpResponse:
        """
        Export user orders to CSV format.
        
        Args:
            profile: User profile
            start_date: Filter from this date
            end_date: Filter until this date
            order_type: Type of order
            product: Specific product filter
            
        Returns:
            HTTP response with CSV file
        """
        orders = TransactionReportService.filter_orders(
            profile=profile,
            start_date=start_date,
            end_date=end_date,
            order_type=order_type,
            product=product
        )
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="orders_{profile.telegram_id}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        # Headers
        writer.writerow([
            'شماره سفارش',
            'تاریخ',
            'محصول',
            'نوع',
            'مقدار (گرم)',
            'قیمت هر گرم',
            'مبلغ کل',
            'وضعیت'
        ])
        
        # Data rows
        for order in orders:
            writer.writerow([
                order.id,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                order.product.name,
                order.get_order_type_display(),
                f"{order.quantity_grams}",
                f"{order.price_per_gram:,.0f}",
                f"{order.total_amount:,.0f}",
                order.get_status_display()
            ])
        
        return response


class PDFExportService:
    """Service for exporting transaction data to PDF format."""
    
    @staticmethod
    def export_transactions_pdf(
        profile: Profile,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None
    ) -> Optional[BytesIO]:
        """
        Export user transactions to PDF format.
        
        Args:
            profile: User profile
            start_date: Filter from this date
            end_date: Filter until this date
            transaction_type: Type of transaction
            
        Returns:
            BytesIO object containing PDF data or None if PDF library unavailable
        """
        if not PDF_AVAILABLE:
            return None
        
        transactions = TransactionReportService.filter_transactions(
            profile=profile,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type
        )
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        # Title
        elements.append(Paragraph(f"Transaction History Report", title_style))
        elements.append(Spacer(1, 12))
        
        # User info
        user_info = [
            ['User:', profile.get_display_name()],
            ['Telegram ID:', profile.telegram_id],
            ['Report Date:', timezone.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        if start_date:
            user_info.append(['Period From:', start_date.strftime('%Y-%m-%d')])
        if end_date:
            user_info.append(['Period To:', end_date.strftime('%Y-%m-%d')])
        
        info_table = Table(user_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Transactions table
        data = [['Date', 'Type', 'Currency', 'Amount', 'Status']]
        
        for txn in transactions[:100]:  # Limit to 100 transactions
            data.append([
                txn.created_at.strftime('%Y-%m-%d %H:%M'),
                txn.get_transaction_type_display(),
                txn.get_currency_display(),
                f"{txn.amount:,.2f}",
                txn.get_status_display()
            ])
        
        table = Table(data, colWidths=[1.5*inch, 1.2*inch, 1*inch, 1.3*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def export_orders_pdf(
        profile: Profile,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_type: Optional[str] = None
    ) -> Optional[BytesIO]:
        """
        Export user orders to PDF format.
        
        Args:
            profile: User profile
            start_date: Filter from this date
            end_date: Filter until this date
            order_type: Type of order
            
        Returns:
            BytesIO object containing PDF data or None if PDF library unavailable
        """
        if not PDF_AVAILABLE:
            return None
        
        orders = TransactionReportService.filter_orders(
            profile=profile,
            start_date=start_date,
            end_date=end_date,
            order_type=order_type
        )
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        # Title
        elements.append(Paragraph(f"Order History Report", title_style))
        elements.append(Spacer(1, 12))
        
        # User info
        user_info = [
            ['User:', profile.get_display_name()],
            ['Telegram ID:', profile.telegram_id],
            ['Report Date:', timezone.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        if start_date:
            user_info.append(['Period From:', start_date.strftime('%Y-%m-%d')])
        if end_date:
            user_info.append(['Period To:', end_date.strftime('%Y-%m-%d')])
        
        info_table = Table(user_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Orders table
        data = [['Order#', 'Date', 'Product', 'Type', 'Qty (g)', 'Price/g', 'Total', 'Status']]
        
        for order in orders[:100]:  # Limit to 100 orders
            data.append([
                str(order.id),
                order.created_at.strftime('%Y-%m-%d'),
                order.product.name[:10],
                'BUY' if order.order_type == Order.OrderType.BUY else 'SELL',
                f"{order.quantity_grams}",
                f"{order.price_per_gram:,.0f}",
                f"{order.total_amount:,.0f}",
                order.get_status_display()[:8]
            ])
        
        table = Table(data, colWidths=[0.5*inch, 1*inch, 1*inch, 0.6*inch, 0.7*inch, 1*inch, 1.2*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer


class BusinessReportService:
    """Service for generating business intelligence and admin reports."""
    
    @staticmethod
    def get_profit_loss_report(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate profit & loss statement based on spread.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary containing P&L data
        """
        orders = Order.objects.filter(status=Order.OrderStatus.COMPLETED)
        
        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        
        if end_date:
            orders = orders.filter(created_at__lte=end_date)
        
        # Calculate profit from spreads
        buy_orders = orders.filter(order_type=Order.OrderType.BUY)
        sell_orders = orders.filter(order_type=Order.OrderType.SELL)
        
        # For buy orders, profit is the difference between buy price charged and actual product buy_price
        # For sell orders, profit is the difference between product sell_price and price paid to user
        
        buy_revenue = Decimal('0')
        for order in buy_orders:
            # User pays at buy_price, we calculate spread based on product prices at time of order
            spread = order.product.get_price_spread()
            buy_revenue += (order.quantity_grams * spread)
        
        sell_revenue = Decimal('0')
        for order in sell_orders:
            # User sells at sell_price, profit is the spread
            spread = order.product.get_price_spread()
            sell_revenue += (order.quantity_grams * spread)
        
        total_revenue = buy_revenue + sell_revenue
        
        return {
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'revenue': {
                'buy_orders': float(buy_revenue),
                'sell_orders': float(sell_revenue),
                'total': float(total_revenue)
            },
            'orders': {
                'buy_count': buy_orders.count(),
                'sell_count': sell_orders.count(),
                'total_count': orders.count()
            },
            'volume': {
                'buy': float(buy_orders.aggregate(total=Sum('total_amount'))['total'] or 0),
                'sell': float(sell_orders.aggregate(total=Sum('total_amount'))['total'] or 0),
                'total': float(orders.aggregate(total=Sum('total_amount'))['total'] or 0)
            }
        }
    
    @staticmethod
    def get_balance_sheet() -> Dict[str, Any]:
        """
        Generate aggregate balance sheet showing total holdings.
        
        Returns:
            Dictionary containing balance sheet data
        """
        profiles = Profile.objects.all()
        
        totals = profiles.aggregate(
            total_rial=Sum('rial_balance'),
            total_gold=Sum('gold_balance'),
            total_coin=Sum('coin_balance'),
            total_dollar=Sum('dollar_balance'),
            frozen_rial=Sum('frozen_rial_balance'),
            frozen_gold=Sum('frozen_gold_balance'),
            frozen_coin=Sum('frozen_coin_balance'),
            frozen_dollar=Sum('frozen_dollar_balance'),
            user_count=Count('id')
        )
        
        return {
            'users': {
                'total': totals['user_count'],
                'active': profiles.filter(is_active=True).count()
            },
            'balances': {
                'rial': {
                    'total': float(totals['total_rial'] or 0),
                    'frozen': float(totals['frozen_rial'] or 0),
                    'available': float((totals['total_rial'] or 0) - (totals['frozen_rial'] or 0))
                },
                'gold': {
                    'total': float(totals['total_gold'] or 0),
                    'frozen': float(totals['frozen_gold'] or 0),
                    'available': float((totals['total_gold'] or 0) - (totals['frozen_gold'] or 0))
                },
                'coin': {
                    'total': float(totals['total_coin'] or 0),
                    'frozen': float(totals['frozen_coin'] or 0),
                    'available': float((totals['total_coin'] or 0) - (totals['frozen_coin'] or 0))
                },
                'dollar': {
                    'total': float(totals['total_dollar'] or 0),
                    'frozen': float(totals['frozen_dollar'] or 0),
                    'available': float((totals['total_dollar'] or 0) - (totals['frozen_dollar'] or 0))
                }
            }
        }
    
    @staticmethod
    def get_user_activity_report(
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate user activity report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary containing user activity data
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Top traders by volume
        top_traders = Profile.objects.annotate(
            total_volume=Sum(
                'orders__total_amount',
                filter=Q(
                    orders__created_at__gte=cutoff_date,
                    orders__status=Order.OrderStatus.COMPLETED
                )
            ),
            order_count=Count(
                'orders',
                filter=Q(
                    orders__created_at__gte=cutoff_date,
                    orders__status=Order.OrderStatus.COMPLETED
                )
            )
        ).filter(
            total_volume__isnull=False
        ).order_by('-total_volume')[:10]
        
        # Dormant users (no activity in the period)
        dormant_users = Profile.objects.annotate(
            recent_orders=Count(
                'orders',
                filter=Q(orders__created_at__gte=cutoff_date)
            )
        ).filter(recent_orders=0, is_active=True)
        
        # New users in the period
        new_users = Profile.objects.filter(
            created_at__gte=cutoff_date
        )
        
        return {
            'period_days': days,
            'top_traders': [
                {
                    'user': trader.get_display_name(),
                    'telegram_id': trader.telegram_id,
                    'total_volume': float(trader.total_volume or 0),  # type: ignore[attr-defined]
                    'order_count': trader.order_count  # type: ignore[attr-defined]
                }
                for trader in top_traders
            ],
            'dormant_users': {
                'count': dormant_users.count(),
                'users': [
                    {
                        'user': user.get_display_name(),
                        'telegram_id': user.telegram_id,
                        'last_active': user.updated_at.isoformat() if user.updated_at else None
                    }
                    for user in dormant_users[:20]
                ]
            },
            'new_users': {
                'count': new_users.count(),
                'users': [
                    {
                        'user': user.get_display_name(),
                        'telegram_id': user.telegram_id,
                        'joined': user.created_at.isoformat()
                    }
                    for user in new_users[:20]
                ]
            }
        }

