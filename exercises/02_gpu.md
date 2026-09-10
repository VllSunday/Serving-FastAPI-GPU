# Exercise 2 — GPU

Цель: убедиться, что модель на нужном device, и посмотреть VRAM.

## Что сделать

1. Проверьте драйвер:

```bash
nvidia-smi
```

2. Запустите сервер и сравните логи:

```text
Device: cuda
GPU: NVIDIA ...
Model: distilgpt2
```

Если CUDA недоступна, будет `Device: cpu`. Сервер всё равно должен работать.

3. Снимите метрики:

```bash
curl http://localhost:8000/gpu
```

Смотрите `allocated_mb` и `reserved_mb`. Это обёртка над:

```python
torch.cuda.memory_allocated()
torch.cuda.memory_reserved()
```

4. Прочитайте `app/model/loader.py` и `app/model/inference.py`.

Там уже есть правильные практики:

```python
model.eval()

with torch.inference_mode():
    ...
```

Тензоры явно переезжают на `bundle.device`. CUDA не захардкожена.

5. Сравните CPU и GPU.

Запустите сервер два раза:

```bash
DEVICE=cpu uvicorn app.main:app --host 0.0.0.0 --port 8000
DEVICE=cuda uvicorn app.main:app --host 0.0.0.0 --port 8000
```

На каждом повторите один и тот же prompt через `client/simple_client.py`. Запишите `latency_ms`.

## Вопросы

1. Что произойдёт, если токенизировать на CPU, а `model.generate()` вызвать на GPU без `.to(device)`?
2. Почему `model.eval()` и `inference_mode()` нужны даже в учебном сервисе?
3. Как связаны размер модели, `max_new_tokens` и VRAM?

```text
batch ↑
sequence length ↑
model size ↑
        ↓
VRAM ↑
```

## Критерий готовности

- вы знаете, на каком device работает ваш процесс
- `/gpu` открывается и на CPU, и на CUDA
- есть хотя бы одна запись latency CPU vs GPU (или пометка, что GPU нет)
