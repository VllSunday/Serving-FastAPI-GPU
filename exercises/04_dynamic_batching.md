# Exercise 4 — Dynamic batching

Это центральная часть занятия.

Клиенты не умеют и не должны склеивать свои запросы. HTTP слой принимает обычный single-request, а GPU получает batch.

```text
Request 1 ─┐
Request 2 ─┤
Request 3 ─┼──→ Queue ──→ Batcher ──→ GPU
Request 4 ─┘
```

Endpoint: `POST /generate/dynamic`

Снаружи как `/generate`. Внутри:

```text
HTTP
 ↓
asyncio.Queue
 ↓
dynamic batcher
 ↓
batch inference
 ↓
individual response
```

## Что открыть

`app/serving/batcher.py`

Там оставлен учебный якорь:

```python
# TODO(student):
# collect requests into a batch
# respect MAX_BATCH_SIZE
# respect MAX_WAIT_MS
# execute one GPU inference
# return each result to the correct request
```

В starter есть рабочая reference-реализация, чтобы занятие можно было показать целиком. Ваша задача — **не пользоваться ею вслепую**.

## Задание

1. Прочитайте `Batcher.submit`, `_collect_batch`, `_execute_and_return`.
2. Удалите тела `_collect_batch` и `_execute_and_return`.
3. Напишите их заново сами.

Правила:

- реальная `asyncio.Queue`, не список в endpoint
- ждать не дольше `MAX_WAIT_MS`
- если набралось `MAX_BATCH_SIZE` — запускать сразу
- один вызов batched inference на пачку
- результат `i` возвращается только запросу `i` через `Future`
- это не цикл `for request in requests: generate_one(...)`

4. В логе batcher должны быть строки вида:

```text
[batcher] batch_size=4 wait_ms=7.2
[batcher] batch_size=8 wait_ms=12.4
```

5. Проверьте под нагрузкой:

```bash
python client/concurrent_client.py \
  --requests 32 \
  --concurrency 8 \
  --endpoint /generate/dynamic
```

Сравните с тем же прогоном на `/generate`.

6. Покрутите параметры:

```bash
MAX_BATCH_SIZE=8 MAX_WAIT_MS=5 uvicorn app.main:app --host 0.0.0.0 --port 8000
MAX_BATCH_SIZE=8 MAX_WAIT_MS=50 uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Маленький `MAX_WAIT_MS` → чаще `batch_size=1`, ниже extra-latency, хуже throughput.
Большой `MAX_WAIT_MS` → крупнее batch, выше throughput, хуже tail latency.

## Почему нужна очередь

HTTP-запросы приходят независимо. GPU один. Если каждый request сразу зовёт `generate()`, вы получаете serial GPU calls и простой железа.

Очередь развязывает lifetime HTTP-запроса и момент, когда GPU свободен набрать пачку.

`async def` здесь только позволяет FastAPI принять много запросов, пока batcher ждёт. Сам CUDA kernel по-прежнему один.

## Вопросы

1. Как результат не перепутается между клиентами?
2. Что будет, если `MAX_WAIT_MS=0`?
3. Почему fake batching (просто for-loop) не считается решением?

## Критерий готовности

- под concurrency=8 в логах бывает `batch_size>1`
- `/batcher/stats` показывает `last_batch_size` и `last_wait_ms`
- каждый клиент получает свой текст
- вы написали collect/execute сами, а не только запустили готовое
