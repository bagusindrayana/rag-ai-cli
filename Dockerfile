FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps (if any) and pip
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . /app

EXPOSE 8000

CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "context-api:app"]
