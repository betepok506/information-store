# Запуск сервера Fast Api


Для работы с ElaticSearch
Расширение ria.elastic



Перед запуском:

Если это первый запуск и база данных не создана:
```
alembic revision --autogenerate
alembic upgrade head
```

Для актуализации структуры базы данных:
```
alembic upgrade head
```

Запуск сервера осуществляется из консоли внутри devcontainer. Команда:
```
gunicorn -w 3 -k uvicorn.workers.UvicornWorker backend.app.main:app  --bind 0.0.0.0:8000 --preload --log-level=debug --timeout 120
```

## Elastic Search

Запрос элемента с Elastic по id
```
curl -X GET   http://elastic_search:9200/text_vectors/_doc/{id}   -H 'Content-Type: application/json
```

Вывод всеъ элементов:
```
curl -X GET   http://localhost:9200/text_vectors/_search   -H 'Content-Type: application/json'
```
