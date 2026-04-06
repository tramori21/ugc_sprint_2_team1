FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=src
ENV APP_PORT=8006

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY pytest.ini ./
COPY migrations ./migrations
COPY src ./src

CMD sh -c "alembic upgrade head && uvicorn main:app --app-dir src --host 0.0.0.0 --port $APP_PORT"