# Exercise 3 — Batch inference

Цель: собрать несколько prompt в один `model.generate()` и измерить эффект.

## Что сделать

1. Прочитайте `generate_batch` в `app/model/inference.py`.

Обратите внимание:

- `tokenizer(..., padding=True)`
- `padding_side = "left"` для decoder-only модели
- `pad_token = eos_token` у GPT-2

2. Вызовите явный batch endpoint:

```bash
curl -X POST http://localhost:8000/generate/batch \
  -H 'Content-Type: application/json' \
  -d '{"prompts":["Explain FastAPI","Explain CUDA","Explain batching"],"max_new_tokens":64}'
```

3. Сравните batch size.

Соберите таблицу для `max_new_tokens=32`:

| batch size | latency_ms одного generate | latency / request | примерный throughput |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 4 | | | |
| 8 | | | |

Для `batch=1` используйте `/generate` или `/generate/batch` с одним prompt.
Для остальных — `/generate/batch`.

4. Сделайте второй эксперимент: один короткий prompt и один очень длинный в одном batch. Сравните latency с batch из двух коротких.

## Что должно получиться

На GPU:

- суммарный throughput почти всегда растёт с batch size
- latency **всего** generate тоже растёт
- latency, нормированная на один prompt, часто падает

Это и есть trade-off **latency vs throughput**.

На CPU рост batch часто почти не помогает или даже мешает.

## Почему padding важен

Разные длины prompt выравниваются до максимума в batch. Короткий prompt «толстеет» pad-токенами. GPU считает и их. Чем больше разброс длин, тем хуже эффективность batch.

## Вопросы

1. Почему для causal LM обычно ставят left padding?
2. Почему 8 отдельных `/generate` медленнее одного `/generate/batch` с 8 prompt?
3. Когда большой batch вреден?

## Критерий готовности

- `/generate/batch` возвращает `results`, `batch_size`, `latency_ms`
- есть таблица для 1 / 2 / 4 / 8
- вы можете объяснить padding и VRAM
