import logging
import os
from pathlib import Path

import redis

from src import checker, poller, state
from src.app import app
from src.models import Channel
from src.talents import load_channels

TALENTS_DIR = Path('/talents')

LOFI_GIRL_CHANNEL_ID = 'UCSJ4gkVC6NrvII8umztf0Ow'
TEST_CHANNELS = [
    Channel(
        id=LOFI_GIRL_CHANNEL_ID,
        name='Lofi Girl',
        group='',
        channel_url=f'https://www.youtube.com/@LofiGirl',
    ),
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)

logger = logging.getLogger(__name__)


def main():
    logger.info('Starting server...')
    state.redis_client = redis.Redis.from_url(
        os.environ.get('REDIS_URL', 'redis://redis:6379')
    )
    state.channels = load_channels(TALENTS_DIR)
    state.test_channels = TEST_CHANNELS
    poller.start()
    checker.start()
    app.run(host='0.0.0.0', port=4656)


if __name__ == '__main__':
    main()
