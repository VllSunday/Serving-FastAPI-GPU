# Exercise 5 — Streaming

Цель: отдать токены по мере генерации, не дожидаясь конца последовательности.

Endpoint: `POST /generate/stream`

## Что сделать

1. Прочитайте `app/serving/streaming.py`.

Там есть TODO:

```python
# TODO(student):
# stream tokens to the client before the full sequence is ready
# do not block the event loop with model.generate()
```

2. Запустите клиент:

```bash
python client/streaming_client.py --prompt "Hello, how are you"
```

Вы должны видеть растущий текст:

```text
Hello
Hello,
Hello, how
Hello, how are
...
```

Сервер шлёт накопленную строку после каждого куска. Это удобнее для занятия, чем сырые дельты.

3. Перепишите генератор сами:

- FastAPI `StreamingResponse`
- Hugging Face `TextIteratorStreamer` или эквивалент
- `model.generate()` в отдельном thread
- event loop не должен стоять на всём generate

4. Пока стримится один запрос, откройте второй терминал и дерните `/health`. Сервер должен ответить, не дожидаясь конца генерации.

## Почему нельзя просто вызвать generate в async def

`model.generate()` — синхронный и долгий. Если вызвать его прямо в coroutine, event loop замирает: другие HTTP-запросы, health, batcher — всё ждёт.

Поэтому generation уезжает в thread, а async-генератор только забирает готовые куски через `asyncio.to_thread(next, iterator)`.

## Вопросы

1. Чем streaming отличается от `/generate` с точки зрения latency до первого токена?
2. Почему streamer + thread, а не один большой `return text`?
3. Можно ли честно стримить и одновременно динамически батчить одну и ту же генерацию? Что здесь сломается?

## Критерий готовности

- клиент печатает текст порциями, не одним блобом в конце
- `/health` отвечает во время стрима
- вы можете указать, какой код не блокирует event loop
