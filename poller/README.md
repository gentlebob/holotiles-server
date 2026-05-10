# poller

Background service that polls YouTube channels for active livestreams and
caches results in Redis. The Flask server (`../server2`) reads from the same
Redis and serves the data over HTTP.

This was split out of `server2` so yt-dlp parsing doesn't contend with HTTP
request handlers for the GIL.
