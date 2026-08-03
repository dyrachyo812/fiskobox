FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY shared /app/shared
COPY bot /app/bot

RUN pip install ./shared ./bot

CMD ["python", "-m", "bot.main"]
