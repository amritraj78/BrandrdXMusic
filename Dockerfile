FROM python:3.10-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    gcc \
    g++ \
    make \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache pip dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel \
    && pip3 install --no-cache-dir -r requirements.txt

# Copy bot source
COPY . /app/

# Expose Koyeb Web Service port
EXPOSE 8000

CMD ["bash", "start"]
