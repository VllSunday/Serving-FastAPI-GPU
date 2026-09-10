# Serving: FastAPI + GPU

Учебный репозиторий для занятия по inference-сервису.

Вы поднимаете локальный FastAPI-сервер, гоняете небольшую causal LM на GPU (или CPU) и руками исследуете batch inference, dynamic batching, streaming и latency/throughput.

Это starter, а не готовый production-фреймворк. Инфраструктура уже запускается. Ключевые места помечены `TODO(student)` — их нужно понять, переписать и измерить.

## 1. Что мы строим

```text
Client
  ↓
FastAPI
  ↓
Queue
  ↓
Dynamic Batcher
  ↓
GPU
  ↓
Model
```

Три режима inference:

| Endpoint | Что происходит |
|---|---|
| `POST /generate` | один запрос → один `model.generate()` |
| `POST /generate/batch` | клиент сам присылает список prompt |
| `POST /generate/dynamic` | обычный single-request API, внутри очередь и batcher |

## 2. Требования

- Python 3.11+
- NVIDIA GPU желательно, но не обязательно
- NVIDIA drivers + CUDA (для GPU-пути)
- Docker — optional

Модель по умолчанию: `distilgpt2` (~82M параметров). Она помещается в обычную consumer GPU, быстро генерирует и даёт увидеть разницу между `batch=1` и `batch>1`.

```text
MODEL_NAME=distilgpt2
DEVICE=auto
```

`DEVICE=auto` выбирает `cuda`, если CUDA доступна, иначе `cpu`. CUDA не захардкожена.

При старте сервер печатает:

```text
Device: cuda
GPU: NVIDIA ...
Model: distilgpt2
```

или:

```text
Device: cpu
Model: distilgpt2
```

## 3. Установка

Не собирайте CUDA вручную. Поставьте готовый wheel PyTorch.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### Linux + NVIDIA GPU

```bash
nvidia-smi
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
```

Если ваш драйвер старше, возьмите другой CUDA index с [pytorch.org](https://pytorch.org/get-started/locally/).

### Windows + WSL2

1. Драйвер NVIDIA ставится в Windows, не внутри WSL.
2. В WSL2 проверьте:

```bash
nvidia-smi
```

3. Дальше как на Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
```

Если `nvidia-smi` в WSL не работает, сначала почините GPU passthrough. Без этого сервер всё равно запустится на CPU.

### CPU fallback

Linux:

```bash
pip install -r requirements-cpu.txt
```

macOS (для локальной проверки без NVIDIA):

```bash
pip install torch
pip install -r requirements.txt
```

На CPU занятие проходится, но разница batch vs single будет слабее: GPU любит широкие тензоры, CPU — нет.

Скопируйте `.env.example` в `.env`, если хотите поменять модель или batcher.

## 4. Запуск

Из корня репозитория:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Первый старт скачает модель из Hugging Face.

### Важно: не поднимайте несколько GPU-worker наугад

```bash
uvicorn app.main:app --workers 4
```

Каждый worker загрузит **свою копию модели**. На GPU это часто значит OOM или 4× VRAM. Для этого занятия оставляйте 1 process.

`async def` тоже не делает GPU-inference параллельным. Одна GPU в каждый момент выполняет один kernel. Очередь нужна как раз для того, чтобы много HTTP-запросов превращались в один широкий kernel, а не в гонку за одним устройством.

## 5. Проверка

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "ok",
  "device": "cuda",
  "gpu": "NVIDIA ...",
  "model": "distilgpt2"
}
```

Простой generate:

```bash
curl -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Explain GPU batching in simple terms","max_new_tokens":64}'
```

## 6. Swagger

Откройте [http://localhost:8000/docs](http://localhost:8000/docs).

Там же удобно руками дергать `/generate`, `/generate/batch`, `/generate/dynamic`, `/generate/stream`.

## 7. GPU verification

```bash
nvidia-smi
```

```bash
curl http://localhost:8000/gpu
```

`/gpu` возвращает device, имя карты, `memory_allocated`, `memory_reserved`. Utilization показывается только если PyTorch умеет его прочитать — это необязательная метрика.

## Endpoints

| Method | Path | Смысл |
|---|---|---|
| GET | `/health` | статус, device, GPU, модель |
| GET | `/gpu` | VRAM |
| GET | `/batcher/stats` | последний batch_size / wait_ms |
| POST | `/generate` | простой single inference |
| POST | `/generate/batch` | явный batch от клиента |
| POST | `/generate/dynamic` | single API + dynamic batching |

Одиночный `/generate/dynamic` почти всегда ждёт весь `MAX_WAIT_MS` — больше некого класть в batch. Это не баг, а цена динамической склейки. Разница видна только под concurrent нагрузкой.
| POST | `/generate/stream` | потоковая генерация |

## Клиенты и benchmark

```bash
python client/simple_client.py --prompt "Explain FastAPI"

python client/concurrent_client.py --requests 32 --concurrency 8
python client/concurrent_client.py --requests 32 --concurrency 8 --endpoint /generate
python client/concurrent_client.py --sweep --endpoint /generate/dynamic

python client/streaming_client.py --prompt "Hello, how are you"
```

`concurrent_client.py` печатает:

```text
requests
successful
failed
total time
average latency
p50
p95
throughput req/s
```

## Почему batch на GPU выгоднее

GPU хорошо утилизируется широкими тензорами. Двадцать отдельных `generate()` с `batch=1` — это двадцать коротких запусков: много overhead, мало работы на SM.

Один `generate()` с `batch=8` загружает больше данных за раз. Throughput (запросов/сек) обычно растёт.

Но:

```text
batch ↑          → throughput ↑
batch ↑          → latency одного запроса часто ↑
batch ↑          → VRAM ↑
sequence length ↑ → VRAM ↑
model size ↑     → VRAM ↑
```

Padding тоже бьёт по эффективности. Если в одном batch лежат короткий и длинный prompt, короткий дополняется pad-токенами до длины самого длинного. Вы платите compute и памятью за «пустые» позиции.

Именно поэтому между HTTP и GPU нужна очередь: независимые клиенты приходят в разное время, а GPU хочет пачку.

## Docker (optional)

Нужен [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

Проверка:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

Затем:

```bash
docker compose up --build
```

Занятие полностью проходится без Docker.

## Задания

Смотрите `exercises/`.

Файлы, которые студент должен читать и менять:

- `app/main.py` — FastAPI endpoints
- `app/model/loader.py` — device, `model.eval()`, перенос на GPU
- `app/model/inference.py` — single и batch generate
- `app/serving/batcher.py` — dynamic batching
- `app/serving/streaming.py` — streaming
- `client/concurrent_client.py` — замеры

## Тесты

```bash
MODEL_NAME=sshleifer/tiny-gpt2 DEVICE=cpu pytest -q
```
