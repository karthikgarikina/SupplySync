import logging

from celery import shared_task
from django.core.cache import cache

from core import constants

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_inventory_updated_event(self, product_id: int, warehouse_id: int, transaction_type: str, quantity: int):
    try:
        logger.info(constants.EVENT_INVENTORY_UPDATED, product_id, warehouse_id, transaction_type, quantity)
        from apps.inventory.services import check_and_publish_low_stock_alert

        check_and_publish_low_stock_alert(product_id, warehouse_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def process_inventory_transfer_event(self, product_id: int, source_warehouse_id: int, destination_warehouse_id: int, quantity: int):
    try:
        logger.info(constants.EVENT_INVENTORY_TRANSFER, product_id, source_warehouse_id, destination_warehouse_id, quantity)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task
def auto_invalidate_low_stock_cache():
    cache.delete(constants.CACHE_KEY_INVENTORY_LOW_STOCK)

