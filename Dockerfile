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
    rm /opt/capsolver/capsolver.zip && \
    echo "=== Capsolver files ===" && \
    ls /opt/capsolver/extension/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Patch nodriver root user check
RUN python -c "
import nodriver.core.browser as b
import inspect
src = inspect.getfile(b)
with open(src, 'r') as f:
    content = f.read()
content = content.replace(
    'if os.getuid() == 0:',
    'if False:  # patched - allow root'
)
with open(src, 'w') as f:
    f.write(content)
print('nodriver patched successfully')
"

COPY scraper.py .

CMD ["python", "scraper.py"]
