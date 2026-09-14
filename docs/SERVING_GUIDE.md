# Конспект: четыре способа сервинга LLM

Этот файл удобно превратить в заметку Rhythm. Он связывает наблюдаемое поведение
dashboard с конкретными участками кода.

## Как читать интерактивную схему

В верхнем блоке dashboard показан фактический маршрут текущего запроса. Статусы
`Client → Queue → Model / GPU → Response` синхронизируются с запросом, а маленькие
маркеры payload позволяют увидеть разницу между одной задачей и группой задач.

Кнопка «Как это работает» открывает учебную вычислительную схему выбранного
режима. «Повторить схему» проигрывает четыре конечных этапа, а нажатие на любой
этап останавливает воспроизведение и показывает его пояснение. Это помогает
отдельно разобрать token ids, padding, форму tensor, GEMM, KV cache и доставку
результата, не перегружая основной экран.

Важно различать два слоя данных:

- `total`, `queue`, `inference`, `batch size`, TTFT и события timeline — реальные
  измерения текущего запуска;
- формы tensor и длительность движения в учебной схеме — намеренно упрощённая
  визуализация механизма, а не profiler trace.

Строка под схемой сообщает реальный runtime. Если проект запущен на CPU,
GPU-блоки объясняют CUDA-механику, но миллисекунды telemetry измерены на CPU.

## Почему `inference_ms` может быть почти одинаковым

В `app/model/inference.py` таймер охватывает ровно один вызов
`model.generate()`. Поэтому смысл числа зависит от режима:

- realtime: время генерации одного prompt с `batch_size=1`;
- offline/dynamic: время генерации всей матрицы `[B × T]` одним вызовом;
- streaming: в UI показываются TTFT и полная latency потока, а не отдельный
  `inference_ms`.

Если одиночный inference и batch inference оба занимают около 13 секунд, это
само по себе нормально. Batch за те же 13 секунд мог обработать четыре prompt,
тогда throughput вырос примерно в четыре раза. Сравнивать нужно одинаковую
работу:

```text
realtime wall time = время четырёх отдельных запросов
batch wall time    = время одного вызова с batch_size=4
throughput         = число готовых prompts / wall time
```

На CPU batch может дать небольшой выигрыш, не дать его совсем или даже стать
медленнее. Основной эффект ожидается на GPU, где широкие матричные операции лучше
загружают вычислительные блоки. На результат также влияют padding, длина output,
размер batch, память и прогрев модели.

Для честного сравнения используйте один prompt, одинаковый лимит токенов и одну
конкурентность:

```bash
python client/concurrent_client.py --requests 4 --concurrency 4 --endpoint /generate --max-new-tokens 16
python client/concurrent_client.py --requests 4 --concurrency 4 --endpoint /generate/dynamic --max-new-tokens 16
```

Контрольный CPU-прогон `Qwen2.5-1.5B-Instruct` на текущей машине дал:

| Режим | Работа | Wall time | Throughput |
|---|---:|---:|---:|
| realtime | 4 отдельных вызова | 15.01 s | 0.27 req/s |
| dynamic | 1 batch из 4 запросов | 5.61 s | 0.71 req/s |

Цифры будут меняться от запуска к запуску, но сравнивать нужно именно весь объём
работы. В этом прогоне dynamic throughput оказался примерно в 2.6 раза выше.

## В каком порядке читать код

1. `app/presentation/api.py` — HTTP-контракты и границы каждого режима.
2. `app/application/serving/realtime.py` — один request/response.
3. `app/application/serving/offline_batch.py` — жизненный цикл offline job.
4. `app/application/serving/continuous_batch.py` — окно, очередь и Future mapping.
5. `app/application/serving/streaming.py` — формирование SSE events.
6. `app/infrastructure/transformers_engine.py` — model lock и Hugging Face adapter.
7. `app/model/inference.py` — tokenization, tensor batch и границы замера.

## 1. Online realtime — `/generate`

```text
HTTP request → RealtimeServing → engine.generate() → JSON response
```

Один запрос приводит к одному вызову модели. FastAPI endpoint асинхронный, но
синхронный inference переносится через `asyncio.to_thread`, поэтому event loop
может продолжать обслуживать `/health` и другие соединения.

Что важно:

- клиент ничего не получает до завершения всей последовательности;
- `latency_ms` включает ожидание model lock, токенизацию, inference и сбор ответа;
- `inference_ms` измеряет сам `model.generate()`;
- в realtime `queue_ms = 0`, а разница с `inference_ms` — токенизация и adapter overhead;
- при большой конкуренции много отдельных `batch=1` вызовов дают слабый GPU
  throughput.

Подходит для простого request/response API, когда низкая latency отдельного
запроса важнее максимальной загрузки GPU.

## 2. Offline batching — `/batch`

```text
POST /batch → 202 + job_id
                    ↓
              asyncio.Queue → worker → generate_batch(prompts)
                    ↓
GET /batch/{id} ← job state/results
```

Это не просто endpoint со списком prompts. Главная семантика offline job:
клиент не держит исходный HTTP request открытым. Он получает идентификатор и
проверяет `queued → running → completed|failed` отдельными запросами.

Почему throughput может быть выше:

- tokenizer выравнивает несколько sequences в один tensor;
- один широкий GPU launch обычно эффективнее нескольких узких;
- системе не нужно сохранять realtime latency каждого отдельного prompt;
- scheduler может собирать крупные однородные jobs.

Цена: результат доступен позже, нужен job storage, retry/idempotency, TTL и
отдельный worker. В лабораторной storage намеренно in-memory, чтобы механизм
был виден без инфраструктурного шума.

Важная метрика — не только latency всего batch, но и:

```text
throughput = completed prompts / wall-clock seconds
latency per item ≈ batch inference time / batch size
```

## 3. Continuous batching — `/generate/dynamic`

```text
request A ─┐                  ┌→ Future A → response A
request B ─┼→ asyncio.Queue →│
request C ─┘   wait window    └→ one generate_batch() → Future B/C
```

Снаружи API остаётся realtime и принимает один prompt. Внутри каждый request
создаёт `Future`, кладёт job в общую очередь и ждёт именно свой future. Worker:

1. Берёт первый job и открывает окно `MAX_WAIT_MS`.
2. Собирает до `MAX_BATCH_SIZE` совместимых job.
3. Один раз вызывает `generate_batch`.
4. Сопоставляет `texts[i]` с `jobs[i].future`.

Почему ответы не путаются: порядок prompts в tensor batch сохраняется, а `zip`
раздаёт результат тому же объекту job. `batch_id` в response позволяет доказать,
что несколько HTTP requests прошли одним model call.

Dashboard отправляет в concurrent-эксперимент один и тот же исходный prompt без
англоязычных служебных суффиксов. Поэтому инструкция отвечать на русском доходит
до модели без искажения. При `do_sample=False` одинаковый prompt закономерно даёт
одинаковый текст во всех четырёх responses: batching меняет форму вычисления, а
не смысл запроса.

Почему нельзя смешать любой набор: generation parameters формируют batch key.
В этой версии проверяется `max_new_tokens`; иначе клиент с лимитом 4 мог бы
получить вычисление на 64 tokens. В production bucket key также включает sampling
settings, adapters, dtype и ограничения sequence length.

Trade-off окна ожидания:

| `MAX_WAIT_MS` | Что чаще происходит | Эффект |
|---|---|---|
| 0–2 ms | batch size 1 | меньше queue latency, ниже throughput |
| 10–30 ms | несколько requests вместе | типичный баланс |
| 50+ ms | batch крупнее | выше throughput, хуже p95 latency |

Это учебная версия continuous batching на уровне **requests**: все sequences в
одном batch завершают вызов вместе. Engines вроде vLLM делают iteration-level
batching — добавляют и удаляют sequences между decode steps.

## 4. Streaming — `/generate/stream`

```text
model.generate(streamer=...) в thread
                  ↓ chunks
TextIteratorStreamer → async SSE generator → browser
```

Response имеет `Content-Type: text/event-stream` и события:

- `start` — соединение принято;
- `token` — новый decoded chunk, накопленный текст и elapsed time;
- `done` — полный текст, число chunks и итоговая latency.

`model.generate()` синхронный. Если вызвать его прямо внутри `async def`, event
loop остановится до конца генерации. Отдельный thread позволяет async generator
забирать готовые chunks и параллельно обслуживать другие HTTP connections.

Streaming уменьшает **TTFT** (time to first token) и воспринимаемую задержку, но
не уменьшает вычислительную стоимость модели. `TextIteratorStreamer` может
буферизовать несколько tokenizer tokens до удобной границы текста, поэтому в UI
точнее говорить «chunk», а не обещать один token на одно событие.

## Общая модель и model lock

Все стратегии используют один `TransformersEngine` и один экземпляр модели.
`threading.Lock` сериализует model calls разных стратегий. Без него два endpoint
могут одновременно занять VRAM, испортить измерения или получить OOM.

Это не означает, что dynamic batcher «последовательный»: внутри его одного
model call находится широкий batch. Lock только запрещает второму независимому
model call конкурировать с первым.

## PyTorch/Hugging Face детали

- `model.eval()` выключает training-поведение вроде dropout.
- `torch.inference_mode()` отключает autograd overhead.
- input tensors переводятся на тот же device, что и модель.
- для decoder-only GPT-2 используется left padding;
- отсутствующий pad token заменяется EOS token;
- instruction-tuned модель получает `system` и `user` через её native chat template;
- после generation input token ids отрезаются, клиент получает только completion;
- FP16 используется на CUDA, FP32 — на CPU.

Padding создаёт скрытую стоимость: один длинный prompt растягивает tensor для
всех коротких prompts в том же batch. Поэтому production scheduler bucket’ит
запросы по близкой длине.

## Эксперименты для самостоятельной проверки

### A. Realtime против dynamic

```bash
python client/concurrent_client.py --requests 32 --concurrency 8 --endpoint /generate
python client/concurrent_client.py --requests 32 --concurrency 8 --endpoint /generate/dynamic
```

Запишите total time, average, p50, p95, req/s и `last_batch_size` из
`/batcher/stats`. На CPU выигрыш может быть мал или отрицателен — это корректный
результат, а не ошибка реализации.

### B. Размер explicit batch

Сравните batch size 1, 2, 4, 8 с одинаковыми prompt length и token limit.

| batch size | inference ms | ms / prompt | prompts / sec | VRAM MB |
|---|---:|---:|---:|---:|
| 1 | | | | |
| 2 | | | | |
| 4 | | | | |
| 8 | | | | |

### C. Padding penalty

Сравните batch из четырёх коротких prompts с batch, где один prompt в 10 раз
длиннее. Объясните изменение через размер padded tensor.

### D. Streaming TTFT

В dashboard сравните `TTFT` и total latency. Во время длинного stream откройте
`/health`: он должен ответить до окончания generation.

## Что улучшать для production

1. Redis/PostgreSQL для offline jobs, TTL, retry и idempotency key.
2. Backpressure: ограниченная очередь и HTTP 429 при перегрузке.
3. Отмена generation при disconnect клиента.
4. Bucketing по prompt length и generation config.
5. Prometheus: queue time, TTFT, tokens/s, p95/p99, batch fill ratio, OOM.
6. Настоящий iteration-level continuous batching через vLLM/TGI/TensorRT-LLM.
7. Несколько replicas с load balancer вместо случайного `uvicorn --workers N`.

Главная мысль: «async» относится к координации запросов, а не делает GPU
вычисления автоматически параллельными. Производительность появляется тогда,
когда scheduler формирует подходящую форму вычисления для accelerator.
