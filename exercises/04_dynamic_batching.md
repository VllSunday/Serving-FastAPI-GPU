# Exercise 4 — Continuous batching

Это центральная часть занятия. Клиенты не склеивают запросы сами: API принимает
обычный single request, а серверный scheduler превращает конкурентные запросы в
один tensor batch.

```text
Request 1 ─┐                      ┌→ Future 1 → response 1
Request 2 ─┼→ asyncio.Queue → GPU ├→ Future 2 → response 2
Request 3 ─┘                      └→ Future 3 → response 3
```

Endpoint: `POST /generate/dynamic`.

## Разбор кода

Откройте `app/application/serving/continuous_batch.py`:

1. `submit` создаёт `DynamicJob` и индивидуальный `Future`.
2. `_collect_compatible` ждёт не дольше `MAX_WAIT_MS`, собирает не больше
   `MAX_BATCH_SIZE` и не смешивает разные `max_new_tokens`.
3. `_execute` вызывает `generate_batch` ровно один раз и раздаёт результаты по
   соответствующим Future.

Поставьте breakpoint перед `_execute` и посмотрите список `batch`. Убедитесь, что
это не fake batching вида `for job: generate_one(job)`.

## Нагрузка

```bash
python client/concurrent_client.py --requests 32 --concurrency 8 --endpoint /generate/dynamic
python client/concurrent_client.py --requests 32 --concurrency 8 --endpoint /generate
```

В логе сервера ожидаются строки:

```text
[continuous-batch] id=1a2b3c4d size=8 wait_ms=6.4 worker_ms=48.2
```

Проверьте `GET /batcher/stats` и сравните `last_batch_size`, `last_wait_ms`, p95
и throughput.

## Эксперимент с окном

```bash
MAX_BATCH_SIZE=8 MAX_WAIT_MS=2 uvicorn app.main:app --port 8000
MAX_BATCH_SIZE=8 MAX_WAIT_MS=50 uvicorn app.main:app --port 8000
```

Малое окно уменьшает добавочную queue latency, но чаще даёт batch size 1.
Большое окно повышает шанс широкого batch, но ухудшает tail latency.

## Вопросы

1. Как `Future` не даёт перепутать ответы клиентов?
2. Почему запросы с разными generation settings нельзя смешивать вслепую?
3. Чем request-level batching отличается от iteration-level batching в vLLM?
4. Почему `async def` сам по себе не ускоряет GPU inference?

## Критерий готовности

- под concurrency 8 появляется `batch_size > 1`;
- несколько response имеют одинаковый `batch_id`;
- каждый клиент получает текст для своего prompt;
- вы можете объяснить latency/throughput trade-off окна ожидания.
