import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

from . import state, store
from .models import Livestream

POLL_INTERVAL = 60 * 60  # seconds

logger = logging.getLogger(__name__)


_FLAT_OPTS = {
    "extract_flat": True,
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
}

_FULL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
}


def _poll_channel(channel):
    url = channel.channel_url + "/streams"
    logger.info("polling %s", channel.name)

    # Stage 1: flat extract to enumerate all entries on the /streams tab.
    try:
        with yt_dlp.YoutubeDL(_FLAT_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        logger.error("error fetching %s: %s", channel.name, e)
        return

    entries = (info or {}).get("entries") or []

    # Stage 2: classify each entry. Flat extraction no longer populates
    # live_status, but it does populate `duration` only for streams that have
    # ended (the recorded length). So:
    #   - duration is not None -> ended (cache the id, never re-extract)
    #   - duration is None     -> live or upcoming; needs a per-entry full
    #                             extract to distinguish (unless we already
    #                             know it's ended via the cache)
    livestreams = []
    upcoming = []
    newly_ended = []

    for entry in entries:
        video_id = entry.get("id")
        if not video_id:
            continue

        if entry.get("duration") is not None:
            newly_ended.append(video_id)
            continue

        if store.is_ended(state.redis_client, channel.id, video_id):
            continue

        video_url = (
            entry.get("url") or f"https://www.youtube.com/watch?v={video_id}"
        )
        try:
            with yt_dlp.YoutubeDL(_FULL_OPTS) as ydl:
                full = ydl.extract_info(video_url, download=False)
        except Exception as e:
            logger.warning("skip %s (%s): %s", video_id, channel.name, e)
            continue

        if not full:
            continue

        stream = Livestream(
            id=video_id,
            title=full.get("title") or entry.get("title", ""),
            url=f"https://www.youtube.com/watch?v={video_id}",
        )
        live_status = full.get("live_status")
        if live_status == "is_live" or full.get("is_live") is True:
            livestreams.append(stream)
        elif live_status == "is_upcoming":
            upcoming.append(stream)
        else:
            # was_live, post_live, not_live, etc. — treat as ended.
            newly_ended.append(video_id)

    if newly_ended:
        store.add_ended(state.redis_client, channel.id, newly_ended)

    store.set_livestreams(state.redis_client, channel.id, livestreams)
    store.set_upcoming(state.redis_client, channel.id, upcoming)

    if livestreams or upcoming:
        logger.info(
            "%s — %d live, %d upcoming", channel.name, len(livestreams), len(upcoming)
        )


def poll_all():
    all_channels = state.channels + state.test_channels
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(_poll_channel, all_channels)
    total_live = sum(
        len(store.get_livestreams(state.redis_client, c.id)) for c in all_channels
    )
    logger.info("poll complete — %d livestreams across all channels", total_live)


def _poll_loop():
    while True:
        poll_all()
        time.sleep(POLL_INTERVAL)


def start():
    t = threading.Thread(target=_poll_loop, daemon=True, name="poller")
    t.start()
