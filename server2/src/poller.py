import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

from . import state, store
from .models import Livestream

POLL_INTERVAL = 60 * 60  # seconds

logger = logging.getLogger(__name__)


def _poll_channel(channel):
    url = channel.channel_url + '/streams'
    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True}
    livestreams = []
    upcoming = []
    logger.info('polling %s', channel.name)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            for entry in info.get('entries', []):
                video_id = entry.get('id')
                if not video_id:
                    continue
                logger.debug('entry %s', video_id)
                stream = Livestream(
                    id=video_id,
                    title=entry.get('title', ''),
                    url=entry.get('url') or f'https://www.youtube.com/watch?v={video_id}',
                )
                live_status = entry.get('live_status')
                if live_status == 'is_live' or entry.get('is_live') is True:
                    livestreams.append(stream)
                elif live_status == 'is_upcoming':
                    upcoming.append(stream)
        except Exception as e:
            logger.error('error fetching %s: %s', channel.name, e)

    store.set_livestreams(state.redis_client, channel.id, livestreams)
    store.set_upcoming(state.redis_client, channel.id, upcoming)

    if livestreams or upcoming:
        logger.info('%s — %d live, %d upcoming', channel.name, len(livestreams), len(upcoming))


def poll_all():
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(_poll_channel, state.channels)
    total_live = sum(
        len(store.get_livestreams(state.redis_client, c.id)) for c in state.channels
    )
    logger.info('poll complete — %d livestreams across all channels', total_live)


def _poll_loop():
    while True:
        poll_all()
        time.sleep(POLL_INTERVAL)


def start():
    t = threading.Thread(target=_poll_loop, daemon=True, name='poller')
    t.start()
