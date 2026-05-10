import logging
import os
import threading
from pathlib import Path

import redis

from src import checker, poller, state
from src.models import Channel
from src.talents import load_channels

TALENTS_DIR = Path('/talents')

LOFI_GIRL_CHANNEL_ID = 'UCSJ4gkVC6NrvII8umztf0Ow'
TEST_CHANNELS = [
    Channel(
        id=LOFI_GIRL_CHANNEL_ID,
        name='Lofi Girl',
        group='',
        channel_url='https://www.youtube.com/@LofiGirl',
    ),
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)

logger = logging.getLogger(__name__)


def main():
    logger.info('Starting poller...')
    state.redis_client = redis.Redis.from_url(
        os.environ.get('REDIS_URL', 'redis://redis:6379')
    )
    state.channels = load_channels(TALENTS_DIR)
    state.test_channels = TEST_CHANNELS
    poller.start()
    checker.start()
    # Block forever; poller and checker run in daemon threads.
    threading.Event().wait()


if __name__ == '__main__':
    main()
