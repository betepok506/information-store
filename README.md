# Information Store

Сервис хранения и управления извлеченной информацией.  
Используется в системах анализа текста, NER, RAG-системах и ИИ-агентах.

### 📌 Основные возможности:
- Хранение документов, сущностей и связей между ними
- REST API для интеграции
- Поддержка поиска по ключевым полям
- Гибкая модель данных (расширяемая под новые типы сущностей)
- Логирование и мониторинг

## 🛠️ Технологии

-  FastAPI
- Python 3.10+
- aio_pika
- PostgreSQL
- SQLAlchemy  
- Docker
- CI/CD
- Prometheus Client
- Logging

## Структура проекта
```
.
├── Dockerfile
├── Makefile
├── alembic  # Миграции
├── alembic.ini
├── app
│   ├── api # API endpoints
│   ├── consumers
│   │   └── handlers
│   │       └── message_handlers.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── healthcheck.py
│   │   └── rabbitmq.py
│   ├── crud # Классы, реализующие CRUD операции
│   ├── db # Скрипты для взаимодействия с БД
│   ├── deps
│   │   └── source_deps.py
│   ├── main.py # Точка входа в программу
│   ├── models # ORM модели
│   ├── publisher.py
│   ├── schemas # Схемы данных
│   ├── services  # Бизнес-логика
│   └── utils   # Утилиты
├── pyproject.toml  # Зависимости проекта 
└── tests # Тесты
```


# Запуск

Перед запуском проекта необходимо создать файл `.env` и задать переменные окружения

### Переменные окружения

|Переменная|По умолчанию|Описание
|----------|----------|----------|
|POSTGRESQL_HOST|database|URI БД|
|POSTGRESQL_USERNAME|postgres|Имя пользователя в БД|
|POSTGRESQL_PASSWORD|postgres|Логин пользователя в БД|
|POSTGRESQL_DATABASE|fastapi_db|Имя БД|
|POSTGRESQL_PORT|5432|Порт для подключения к БД|
|ELASTIC_SEARCH_DATABASE_HOST|elastic_search|URI адресс ElasticSearch|
|ELASTIC_SEARCH_DATABASE_PORT|9200|Порт ElasticSearch|


Сборка и запуск сервиса:
```
docker-compose -p prod-information-store up --build
```

Остановка сервиса:
```
docker-compose down
```

[Информация по разворачиванию](deployment.md)
[Информация по разработке](development.md)
