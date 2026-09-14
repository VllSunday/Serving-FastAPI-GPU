# Exercise 5 — Streaming

Цель: получить первые части текста до завершения всей последовательности и не
заблокировать FastAPI event loop.

Endpoint: `POST /generate/stream`.

## Разбор кода

Откройте два уровня:

- `app/application/serving/streaming.py` превращает chunks в SSE events;
- `app/infrastructure/transformers_engine.py` запускает Hugging Face
  `TextIteratorStreamer` и `model.generate()` в отдельном thread.

Путь данных:

```text
generation thread → TextIteratorStreamer → async generator → StreamingResponse
```

Сервер отправляет события `start`, `token`, `done`. В `token` находятся:

- `delta` — новый decoded chunk;
- `text` — накопленный текст;
- `elapsed_ms` — время с начала запроса.

Chunk не обязан совпадать с одним tokenizer token: streamer может буферизовать
текст до удобной границы декодирования.

## Запуск

```bash
python client/streaming_client.py --prompt "Explain token streaming"
```

Во втором терминале во время длинной генерации вызовите:

```bash
curl http://127.0.0.1:8000/health
```

Health должен ответить до завершения stream. Если вызвать синхронный
`model.generate()` прямо в coroutine, весь event loop будет ждать.

## Вопросы

1. Чем TTFT отличается от total latency?
2. Почему streaming улучшает восприятие скорости, но не ускоряет вычисления?
3. Зачем нужны `Cache-Control: no-cache` и `X-Accel-Buffering: no`?
4. Почему честно совместить streaming и простой request-level dynamic batcher
   сложнее, чем реализовать их отдельно?

## Критерий готовности

- текст появляется частями до события `done`;
- dashboard показывает TTFT и количество chunks;
- `/health` отвечает во время stream;
- вы можете показать строку, которая переносит generation из event loop.
