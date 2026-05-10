import json
import logging
import re
from pathlib import Path

from .models import Channel

logger = logging.getLogger(__name__)


def load_channels(talents_dir: Path) -> list[Channel]:
    channels = []
    for path in sorted(talents_dir.glob('*.json')):
        data = json.loads(path.read_text())
        if data.get('status') != 'Active':
            continue
        yt_url = data.get('YouTube')
        if not yt_url:
            continue
        match = re.search(r'/channel/(UC[\w-]+)', yt_url)
        if not match:
            continue
        channel_id = match.group(1)
        channels.append(Channel(
            id=channel_id,
            name=data.get('name_en', path.stem),
            group=data.get('group', ''),
            channel_url=f'https://www.youtube.com/channel/{channel_id}',
        ))
    logger.info('%d active channels loaded', len(channels))
    return channels
