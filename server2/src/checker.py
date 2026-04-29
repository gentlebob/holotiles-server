import logging
import threading
import time

import yt_dlp

from . import state, store

CHECK_INTERVAL = 30  # seconds

logger = logging.getLogger(__name__)


def _get_live_status(video_url: str) -> str | None:
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('live_status') if info else None
    except Exception as e:
        logger.error('error checking %s: %s', video_url, e)
        return None


def _check_loop():
    while True:
        time.sleep(CHECK_INTERVAL)

        for channel in state.channels:
            livestreams = store.get_livestreams(state.redis_client, channel.id)
            upcoming = store.get_upcoming(state.redis_client, channel.id)

            # Check live streams — remove any that are no longer live
            for stream in livestreams:
                status = _get_live_status(stream.url)
                if status != 'is_live':
                    logger.info('%r ended (status=%s)', stream.title, status)
                    store.remove_livestream(state.redis_client, channel.id, stream.id)

            # Check upcoming — promote to live or remove if disappeared
            for stream in upcoming:
                status = _get_live_status(stream.url)
                if status == 'is_live':
                    logger.info('%r is now live', stream.title)
                    store.move_upcoming_to_live(state.redis_client, channel.id, stream.id)
                elif status != 'is_upcoming':
                    logger.info('%r disappeared (status=%s)', stream.title, status)
                    store.remove_upcoming(state.redis_client, channel.id, stream.id)


def start():
    t = threading.Thread(target=_check_loop, daemon=True, name='checker')
    t.start()
