FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Edge browser
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    curl \
    ca-certificates \
    # Add Microsoft Edge repository (new method without apt-key)
    && wget -q https://packages.microsoft.com/keys/microsoft.asc -O /usr/share/keywares/microsoft-edge.asc \
    && echo "deb [arch=amd64 signed-by=/usr/share/keywares/microsoft-edge.asc] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends microsoft-edge-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "--mode", "monitor"]
