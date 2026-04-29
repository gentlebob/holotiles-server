FROM python:3.13-alpine

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

# Run scraper once on startup, then hand off to cron
RUN printf '#!/bin/sh\ncd /app && uv run python src/hololive_scraper.py\nexec crond -f -l 2\n' \
    > /entrypoint.sh && chmod +x /entrypoint.sh

# Run every 24 hours at midnight
RUN echo "0 0 * * * cd /app && uv run python src/hololive_scraper.py >> /var/log/updater.log 2>&1" \
    > /etc/crontabs/root

CMD ["/entrypoint.sh"]
