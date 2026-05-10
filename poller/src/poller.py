import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

from . import state, store
from .models import Livestream

POLL_INTERVAL = 60 * 60  # seconds
CHANNEL_WORKERS = 10  # parallel /streams listings
VIDEO_WORKERS = 20    # parallel per-video full extracts

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


def _poll_video(video_id: str):
    """Full-extract one video and classify it. Returns one of:
       ('live',     Livestream)
       ('upcoming', Livestream)
       ('ended',    video_id)
       (None, None) on error / missing info.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(_FULL_OPTS) as ydl:
            full = ydl.extract_info(video_url, download=False)
    except Exception as e:
        logger.warning("skip %s: %s", video_id, e)
        return (None, None)

    if not full:
        return (None, None)

    stream = Livestream(
        id=video_id,
        title=full.get("title", ""),
        url=video_url,
    )
    live_status = full.get("live_status")
    if live_status == "is_live" or full.get("is_live") is True:
        return ("live", stream)
    if live_status == "is_upcoming":
        return ("upcoming", stream)
    # was_live, post_live, not_live, etc. — treat as ended.
    return ("ended", video_id)


def _poll_channel(channel, video_pool):
    """Stage 1: flat-extract /streams. For each entry that needs a full extract
    to determine status, submit a _poll_video task to `video_pool`. Wait for
    those tasks, then persist this channel's results to Redis."""
    url = channel.channel_url + "/streams"
    logger.info("polling %s", channel.name)

    try:
        with yt_dlp.YoutubeDL(_FLAT_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        logger.error("error fetching %s: %s", channel.name, e)
        return

    entries = (info or {}).get("entries") or []

    # In flat extract, `duration is not None` means the stream has ended
    # (the value is the recorded length). Anything else is live-or-upcoming
    # and needs a per-video full extract to distinguish — unless we've
    # already cached it as ended on a previous poll.
    newly_ended = []
    futures = []
    for entry in entries:
        video_id = entry.get("id")
        if not video_id:
            continue
        if entry.get("duration") is not None:
            newly_ended.append(video_id)
            continue
        if store.is_ended(state.redis_client, video_id):
            continue
        futures.append(video_pool.submit(_poll_video, video_id))

    livestreams = []
    upcoming = []
    for fut in futures:
        kind, payload = fut.result()
        if kind == "live":
            livestreams.append(payload)
        elif kind == "upcoming":
            upcoming.append(payload)
        elif kind == "ended":
            newly_ended.append(payload)

    if newly_ended:
        store.add_ended(state.redis_client, newly_ended)
    store.set_livestreams(state.redis_client, channel.id, livestreams)
    store.set_upcoming(state.redis_client, channel.id, upcoming)

    if livestreams or upcoming:
        logger.info(
            "%s — %d live, %d upcoming", channel.name, len(livestreams), len(upcoming)
        )


def poll_all():
    all_channels = state.channels + state.test_channels

    # Outer pool runs the per-video stage; inner pool runs per-channel work
    # which submits into the outer pool. The inner `with` exits first
    # (channel pool drains), then the outer (video pool drains).
    with ThreadPoolExecutor(max_workers=VIDEO_WORKERS) as video_pool:
        with ThreadPoolExecutor(max_workers=CHANNEL_WORKERS) as channel_pool:
            list(channel_pool.map(lambda ch: _poll_channel(ch, video_pool), all_channels))

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
