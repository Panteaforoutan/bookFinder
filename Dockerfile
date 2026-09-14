FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p uploads
COPY . .
EXPOSE 5001
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
