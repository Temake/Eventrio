FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE = 1
ENV PYTHONUNBUFFERED = 1
RUN apt-get update && apt-get install -y gcc python3-dev libpq-dev


WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .


CMD ["gunicorn", "--bind", "0.0.0:8000", "--workers", "4", "main.wsgi:application"]