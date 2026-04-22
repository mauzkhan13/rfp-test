FROM python:3.13-slim-bookworm

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
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY CapSolver.Browser.Extension-chrome-v1.17.0.zip /opt/capsolver/capsolver.zip
RUN unzip /opt/capsolver/capsolver.zip -d /opt/capsolver/extension && \
    rm /opt/capsolver/capsolver.zip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY patch_nodriver.py .
RUN python patch_nodriver.py

COPY scraper.py .

# Run as non-root — this bypasses nodriver root check entirely
RUN useradd -m -u 1000 scraper && \
    chown -R scraper:scraper /app && \
    chown -R scraper:scraper /opt/capsolver

USER scraper

CMD ["python", "scraper.py"]
