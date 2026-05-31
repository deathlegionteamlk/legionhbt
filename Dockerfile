FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN cd ui && npm install && npm run build

EXPOSE 8080 8081 8082 8083

CMD ["python", "main.py"]
