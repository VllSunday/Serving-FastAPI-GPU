# Exercise 1 — FastAPI

Цель: поднять сервер и понять самый простой inference API.

## Что сделать

1. Создайте venv и поставьте зависимости (GPU или CPU, см. README).
2. Запустите сервер:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3. Откройте `/docs`.
4. Проверьте `/health`.
5. Отправьте `POST /generate`.

```bash
python client/simple_client.py
```

## Разбор кода

Прочитайте:

- `app/main.py` — `/health` и `/generate`
- `app/serving/simple.py`
- `app/model/inference.py` → `generate_one`

Путь запроса:

```text
HTTP request
    ↓
model.generate()
    ↓
response
```

Здесь ещё нет очереди и нет batching. Один клиент занимает модель целиком.

## Вопросы

1. Что возвращает `/health`, если CUDA нет?
2. Почему `latency_ms` считается на сервере, а не только в клиенте?
3. Что будет, если запустить `uvicorn --workers 4`?

## Критерий готовности

- `/health` отвечает `status=ok`
- `/generate` возвращает `text` и `latency_ms`
- вы можете объяснить, где вызывается `model.generate()`
