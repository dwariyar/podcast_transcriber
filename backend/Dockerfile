FROM python:3.11-slim-buster

WORKDIR /app

ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8

RUN apt-get update && apt-get install -y ffmpeg \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

# If requirements.txt doesn't change, this layer is cached, speeding up builds
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5001", "app:app", "--worker-class", "gevent"]