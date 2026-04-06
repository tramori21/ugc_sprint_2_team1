# UGC Sprint 2

Ссылка на репозиторий - https://github.com/tramori21/ugc_sprint_2_team1

Сервис для работы с пользовательским UGC: лайки, закладки, рецензии, события просмотров, ETL и инфраструктура наблюдаемости.

## Состав проекта

- `auth` — сервис авторизации и работы с пользователями
- `ugc_api` — API для пользовательских действий и UGC
- `ugc_etl` — чтение событий из Kafka и запись в ClickHouse
- `MongoDB` — хранение лайков, закладок и рецензий
- `PostgreSQL` — данные auth-сервиса
- `Kafka` — шина событий
- `ClickHouse` — аналитическое хранилище просмотров
- `ELK` — сбор и просмотр логов
- `Sentry` — сбор ошибок

## Что сделано

### 1. Исследование хранилища для UGC

Для сравнения MongoDB и PostgreSQL сделаны скрипты:

- `scripts/generate_ugc_benchmark_data.py`
- `scripts/benchmark_ugc_storage.py`

Финальный запуск:

```powershell
.\.venv\Scripts\python.exe .\scripts\benchmark_ugc_storage.py --rows 10000000 --chunk-size 500
```

Результаты:

- `POSTGRES_INSERT_MS=578100.41`
- `MONGO_INSERT_MS=340220.5`
- `POSTGRES_USER_BOOKMARKS_MS=4.77`
- `MONGO_USER_BOOKMARKS_MS=3.32`
- `POSTGRES_MOVIE_AVG_RATING_MS=3.1`
- `MONGO_MOVIE_AVG_RATING_MS=1.66`

В этом прогоне MongoDB оказалась быстрее на массовой вставке и на сценариях чтения.

### 2. CRUD API для UGC

Реализован CRUD для:

- bookmarks
- likes
- reviews

Интеграционные тесты:

- `tests/test_ugc_crud_integration.py`

### 3. CI

Добавлен workflow:

- `.github/workflows/ci.yml`

Проверки:

- `ruff`
- `mypy`
- `pytest`

### 4. ELK

Подключены:

- `Elasticsearch`
- `Logstash`
- `Kibana`

Логи сервисов отправляются в Logstash и доступны в Elasticsearch и Kibana.

### 5. Sentry

Поднят self-hosted Sentry.
Для сервисов настроена отправка ошибок.

## Структура проекта

```text
.
├── src/
├── ugc_api/
├── ugc_etl/
├── tests/
├── scripts/
├── elk/
├── .github/workflows/
├── docker-compose.yml
├── pyproject.toml
├── mypy.ini
└── README.md
```

## Запуск проекта

```powershell
docker compose up -d --build
```

## Проверка health

```powershell
Invoke-WebRequest http://127.0.0.1:8006/health -Headers @{ "X-Request-Id" = "health-auth" }
Invoke-WebRequest http://127.0.0.1:8010/health -Headers @{ "X-Request-Id" = "health-ugc" }
```

## Запуск тестов

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Статический анализ

```powershell
.\.venv\Scripts\python.exe -m ruff check src ugc_api/src ugc_etl/src tests
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m mypy ugc_api/src
.\.venv\Scripts\python.exe -m mypy ugc_etl/src
```

## Текущее состояние

Сделаны:

- исследование MongoDB vs PostgreSQL для UGC
- CRUD API для лайков, закладок и рецензий
- CI с основными проверками
- ELK
- Sentry

Последний локальный прогон тестов:

- `6 passed`
