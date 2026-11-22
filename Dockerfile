FROM python:3.12-slim

# ffmpeg wajib untuk menggabungkan stream video+audio pada resolusi tinggi
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/

WORKDIR /app/backend

ENV PORT=8080
EXPOSE 8080

CMD ["gunicorn", "-w", "2", "--timeout", "120", "-b", "0.0.0.0:8080", "app:app"]
