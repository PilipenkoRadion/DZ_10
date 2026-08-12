import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("booksite_functions")

CACHE_KEY_TEMPLATE = "kronyr:channel_stats:{channel_id}"
CACHE_TIMEOUT = 60 * 15  # 15 минут


def get_channel_stats(channel_id=None):
    """Возвращает статистику Telegram-канала из Kronyr или None при недоступности."""
    channel_id = channel_id or settings.KRONYR_CHANNEL_ID
    cache_key = CACHE_KEY_TEMPLATE.format(channel_id=channel_id)

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if not settings.KRONYR_SERVICE_TOKEN:
        logger.warning("KRONYR_SERVICE_TOKEN не задан — блок статистики скрыт")
        return None

    try:
        response = requests.get(
            f"{settings.KRONYR_API_URL}/api/channels/{channel_id}/",
            headers={"Authorization": f"Bearer {settings.KRONYR_SERVICE_TOKEN}"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error("Kronyr API недоступен: %s", e)
        return None

    cache.set(cache_key, data, CACHE_TIMEOUT)
    return data