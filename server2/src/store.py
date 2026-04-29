import json

import redis

from .models import Livestream


def _live_key(channel_id: str) -> str:
    return f'channel:{channel_id}:livestreams'


def _upcoming_key(channel_id: str) -> str:
    return f'channel:{channel_id}:upcoming'


def _encode(stream: Livestream) -> str:
    return json.dumps({'id': stream.id, 'title': stream.title, 'url': stream.url})


def _decode(data: bytes) -> Livestream:
    return Livestream(**json.loads(data))


def set_livestreams(r: redis.Redis, channel_id: str, streams: list[Livestream]) -> None:
    key = _live_key(channel_id)
    pipe = r.pipeline()
    pipe.delete(key)
    for s in streams:
        pipe.hset(key, s.id, _encode(s))
    pipe.execute()


def get_livestreams(r: redis.Redis, channel_id: str) -> list[Livestream]:
    return [_decode(v) for v in r.hvals(_live_key(channel_id))]


def remove_livestream(r: redis.Redis, channel_id: str, stream_id: str) -> None:
    r.hdel(_live_key(channel_id), stream_id)


def set_upcoming(r: redis.Redis, channel_id: str, streams: list[Livestream]) -> None:
    key = _upcoming_key(channel_id)
    pipe = r.pipeline()
    pipe.delete(key)
    for s in streams:
        pipe.hset(key, s.id, _encode(s))
    pipe.execute()


def get_upcoming(r: redis.Redis, channel_id: str) -> list[Livestream]:
    return [_decode(v) for v in r.hvals(_upcoming_key(channel_id))]


def remove_upcoming(r: redis.Redis, channel_id: str, stream_id: str) -> None:
    r.hdel(_upcoming_key(channel_id), stream_id)


def move_upcoming_to_live(r: redis.Redis, channel_id: str, stream_id: str) -> None:
    up_key = _upcoming_key(channel_id)
    data = r.hget(up_key, stream_id)
    if data:
        pipe = r.pipeline()
        pipe.hdel(up_key, stream_id)
        pipe.hset(_live_key(channel_id), stream_id, data)
        pipe.execute()
