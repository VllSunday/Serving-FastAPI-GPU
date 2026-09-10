# Exercise 6 — Load testing

Цель: измерить систему, а не «на глаз».

Не нужен Locust/k6. Достаточно `client/concurrent_client.py`.

## Эксперимент A — sequential vs concurrent

Одинаковые 10 запросов, `max_new_tokens=32`, endpoint `/generate`:

```bash
python client/concurrent_client.py --requests 10 --concurrency 1 --endpoint /generate
python client/concurrent_client.py --requests 10 --concurrency 10 --endpoint /generate
```

Запишите total time, average latency, p95, throughput.

Повторите то же на `/generate/dynamic`.

## Эксперимент B — batch size

Явный batch:

| batch size | latency_ms | notes |
|---|---|---|
| 1 | | `/generate` или batch из 1 prompt |
| 4 | | `/generate/batch` |
| 8 | | `/generate/batch` |

И dynamic batching под нагрузкой:

```bash
python client/concurrent_client.py --requests 32 --concurrency 8 --endpoint /generate/dynamic
```

Смотрите серверные логи:

```text
[batcher] batch_size=...
```

и `GET /batcher/stats`.

## Эксперимент C — sweep

```bash
python client/concurrent_client.py --sweep --endpoint /generate
python client/concurrent_client.py --sweep --endpoint /generate/dynamic
```

Это прогон concurrency `1 2 4 8 16 32`.

## Что писать в отчёт

Для каждой строки:

- requests
- successful
- failed
- total time
- average latency
- p50
- p95
- throughput req/s

И короткий вывод:

1. Где выигрывает throughput?
2. Где проигрывает latency?
3. Виден ли реальный batch в логах (`batch_size>1`)?
4. Что случилось с VRAM на `/gpu`?

## Ожидаемая картина

На GPU:

- sequential `/generate` — низкая per-request latency, слабый throughput
- concurrent `/generate` — запросы всё равно выстраиваются у одной модели, p95 растёт
- concurrent `/generate/dynamic` — в логах пачки, throughput выше
- большой batch — больше req/s и больше latency/VRAM

Если цифры «странные», сначала проверьте, что вы не на CPU и не держите `--workers > 1`.

## Критерий готовности

- есть таблица A и таблица B
- есть сравнение `/generate` vs `/generate/dynamic`
- вывод сформулирован в терминах latency vs throughput, а не «быстрее/медленнее»
