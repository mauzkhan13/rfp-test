FROM python:3.13-slim-bookworm

# Install Chromium + Xvfb
RUN apt-get update && apt-get install -y \
    chromium \
    xvfb \
    x11-utils \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper.py .

CMD ["python", "scraper.py"]
