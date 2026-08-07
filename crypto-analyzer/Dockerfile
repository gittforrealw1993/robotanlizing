FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Edge browser
RUN apt-get update && \
 apt-get install -y wget gnupg curl && \
 mkdir -p /etc/apt/keyrings && \
 wget -q https://packages.microsoft.com/keys/microsoft.asc -O /etc/apt/keyrings/microsoft.gpg && \
 echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge.list && \
 apt-get update && \
 apt-get install -y microsoft-edge-stable && \
 apt-get clean && \
 rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "--mode", "monitor"]
