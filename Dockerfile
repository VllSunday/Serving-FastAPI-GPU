FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.hf_cache \
    MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct \
    DEVICE=cuda \
    MAX_BATCH_SIZE=8 \
    MAX_WAIT_MS=20

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY client ./client

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
