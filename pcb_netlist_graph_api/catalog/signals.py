from __future__ import annotations

from typing import Any

from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from catalog.models import Component


@receiver(post_save, sender=Component)
def invalidate_component_cache(
    sender: type[Component], instance: Component, **kwargs: Any
) -> None:
    cache.clear()
