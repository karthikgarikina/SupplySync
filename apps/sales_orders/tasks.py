import logging

from celery import shared_task
from django.utils import timezone

from core import constants

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_sales_order_created_event(self, order_id: int, created_by_user_id: int):
    try:
        logger.info(constants.EVENT_SO_CREATED, order_id, created_by_user_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def process_sales_order_cancelled_event(self, order_id: int):
    try:
        logger.info(constants.EVENT_SO_CANCELLED, order_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task
def generate_daily_operations_summary():
    from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderStatus
    from apps.sales_orders.models import SalesOrder, SalesOrderStatus

    today = timezone.localdate()
    new_pos = PurchaseOrder.objects.filter(created_at__date=today).count()
    pos_received = PurchaseOrder.objects.filter(status=PurchaseOrderStatus.RECEIVED, actual_delivery_date=today).count()
    new_sales_orders = SalesOrder.objects.filter(created_at__date=today).count()
    orders_dispatched = SalesOrder.objects.filter(status=SalesOrderStatus.DISPATCHED, dispatched_at__date=today).count()
    orders_delivered = SalesOrder.objects.filter(status=SalesOrderStatus.DELIVERED, delivered_at__date=today).count()
    logger.info(constants.DAILY_SUMMARY_LOG, today, new_pos, pos_received, new_sales_orders, orders_dispatched, orders_delivered)

