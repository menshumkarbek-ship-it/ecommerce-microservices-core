from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Category


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, **kwargs):
    """Keep the cached category list fresh so a new category (and its
    homepage slideshow / catalog filter option) appears immediately,
    regardless of whether it was created via the branded form or admin."""
    cache.delete('global_store_categories')
