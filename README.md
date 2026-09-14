# LLM Serving Lab: FastAPI + GPU

Учебный проект с четырьмя **реально различающимися** способами сервинга одной
causal language model. Проект запускается на NVIDIA GPU или CPU и показывает
очередь, batch size, latency, streaming chunks и жизненный цикл offline job.

Откройте `http://127.0.0.1:8000/` после запуска — dashboard позволяет пройти
все эксперименты без ручного `curl`. OpenAPI остаётся на `/docs`.

## Четыре стратегии

| API | Механизм | Что оптимизируем |
|---|---|---|
| `POST /generate` | один request → один `generate()` → один JSON | latency одного запроса |
| `POST /batch` | job id → фоновая очередь → один явный tensor batch | throughput без realtime SLA |
| `POST /generate/dynamic` | независимые requests → короткое окно → общий batch | throughput при realtime API |
| `POST /generate/stream` | generation thread → SSE `token` events | time to first token |

`POST /generate/dinamic` оставлен как скрытый alias для написания из задания.
Старый `POST /generate/batch` тоже работает, но новый offline-контракт — `/batch`.

## Clean architecture

```text
presentation (FastAPI + browser UI)
             ↓
application/serving (4 use cases) → application/ports.py
             ↓                            ↑
domain (commands, results, job state)     │
                                          │ implements
infrastructure/transformers_engine.py ────┘
             ↓
model (Hugging Face loader + tensor inference)
```

`app/main.py` — только composition root: создаёт модель, адаптер и use cases.
Ни одна стратегия не импортирует FastAPI, PyTorch или Transformers. Поэтому их
можно тестировать fake engine без загрузки модели.

Где смотреть каждую реализацию:

- realtime — `app/application/serving/realtime.py`;
- offline batching — `app/application/serving/offline_batch.py`;
- continuous batching — `app/application/serving/continuous_batch.py`;
- streaming — `app/application/serving/streaming.py` и низкоуровневый streamer
  в `app/infrastructure/transformers_engine.py`;
- HTTP-контракты — `app/presentation/api.py`;
- dashboard — `app/presentation/static/`.

Подробный разбор для конспекта: [`docs/SERVING_GUIDE.md`](docs/SERVING_GUIDE.md).

## Быстрый старт

Требования: Python 3.11+, NVIDIA GPU желательно, но не обязательно.

### CPU

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-cpu.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### NVIDIA GPU

Проверьте `nvidia-smi`, установите подходящий готовый wheel PyTorch с
`pytorch.org`, затем:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Не запускайте несколько Uvicorn workers без расчёта VRAM: каждый process
загрузит собственную копию модели. Для лабораторной используйте один worker.

Настройки из `.env`:

```dotenv
MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
DEVICE=auto
SYSTEM_PROMPT=You are a factual assistant demonstrating model inference serving. Answer directly in the same language as the user, using 1-3 concise sentences unless asked otherwise. Never repeat the user's prompt. For machine-learning topics, clearly distinguish inference from training.
MAX_BATCH_SIZE=8
MAX_WAIT_MS=20
DEFAULT_MAX_NEW_TOKENS=64
MAX_NEW_TOKENS_CAP=128
```

Если на GPU достаточно памяти и важнее качество текста, модель можно заменить
без изменений в коде, например: `MODEL_NAME=Qwen/Qwen2.5-3B-Instruct`.

## Проверка из терминала

```bash
python client/simple_client.py
python client/offline_batch_client.py
python client/concurrent_client.py --requests 32 --concurrency 8 --endpoint /generate/dynamic
python client/streaming_client.py
python -m pytest -q
```

Health и GPU telemetry:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/gpu
curl http://127.0.0.1:8000/batcher/stats
```

## Ограничения учебной реализации

- Offline jobs хранятся в памяти и исчезают после рестарта. Для production
  понадобятся PostgreSQL/Redis и отдельный worker.
- Один process владеет одной моделью; model lock не даёт разным стратегиям
  одновременно спорить за ту же GPU.
- Continuous batcher объединяет только запросы с одинаковым
  `max_new_tokens`. Production engines обычно bucket’ят больше параметров.
- SSE chunks — куски декодированного текста, а не гарантированно один tokenizer
  token на событие. Это особенность `TextIteratorStreamer`.
- Модель по умолчанию — instruction-tuned `Qwen/Qwen2.5-1.5B-Instruct`.
  Для неё применяется native chat template. Она заметно тяжелее GPT-2 starter,
  но всё ещё достаточно мала для учебного запуска.
