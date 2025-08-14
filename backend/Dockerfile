FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8

# If requirements.txt doesn't change, this layer is cached, speeding up builds
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001"]