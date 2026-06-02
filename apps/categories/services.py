from django.core.cache import cache

from apps.categories.models import Category
from core import constants
from core.exceptions import DuplicateResourceException, ResourceNotFoundException
from core.utils import random_upper_code


def _invalidate_category_cache():
    cache.delete(constants.CACHE_KEY_CATEGORIES_TREE)


def _generate_category_code():
    while True:
        code = f"{constants.CODE_PREFIX_CATEGORY}-{random_upper_code(constants.SHORT_CODE_LENGTH)}"
        if not Category.all_objects.filter(category_code=code).exists():
            return code


def create_category(data: dict) -> Category:
    """Create a category and invalidate the cached category tree."""
    parent = None
    parent_id = data.pop("parent_category_id", None)
    if parent_id:
        try:
            parent = Category.objects.get(id=parent_id)
        except Category.DoesNotExist as exc:
            raise ResourceNotFoundException("Parent category not found.") from exc
    code = data.get("category_code") or _generate_category_code()
    if Category.all_objects.filter(category_code=code).exists():
        raise DuplicateResourceException("Category code already exists.", code=constants.ERROR_DUPLICATE_RESOURCE)
    category = Category.objects.create(**{**data, "category_code": code, "parent_category": parent})
    _invalidate_category_cache()
    return category


def list_categories():
    """Return all non-deleted categories."""
    return Category.objects.order_by("id")


def get_category_tree() -> list:
    """Return root categories used by CategoryTreeSerializer for recursive output."""
    cached = cache.get(constants.CACHE_KEY_CATEGORIES_TREE)
    if cached is not None:
        return cached
    categories = list(Category.objects.filter(parent_category__isnull=True).order_by("id"))
    cache.set(constants.CACHE_KEY_CATEGORIES_TREE, categories, timeout=constants.CATEGORY_TREE_CACHE_TTL)
    return categories

