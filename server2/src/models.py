from dataclasses import dataclass


@dataclass
class Livestream:
    id: str
    title: str
    url: str


@dataclass
class Channel:
    id: str
    name: str
    group: str
    channel_url: str
