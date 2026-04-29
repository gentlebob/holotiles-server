import redis

from .models import Channel

channels: list[Channel] = []
redis_client: redis.Redis
