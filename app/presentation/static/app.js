const modes = {
  realtime: {
    endpoint: "POST /generate",
    title: "Online realtime",
    summary: "Запрос сразу занимает модель и возвращается только после полной генерации.",
    priority: "минимальная latency",
    hint: "Ответ появится целиком: промежуточных частей клиент не увидит.",
    promptLabel: "Prompt",
    button: "Запустить realtime",
    stages: ["client", "model", "response"],
    observations: ["Один HTTP-запрос создаёт ровно один вызов generate().", "Клиент ждёт весь ответ, поэтому TTFT равен почти полной latency.", "Под высокой конкуренцией отдельные вызовы спорят за одну модель."],
  },
  batch: {
    endpoint: "POST /batch  →  GET /batch/{id}",
    title: "Offline batch",
    summary: "Клиент отдаёт набор задач, получает job id и забирает результат позже.",
    priority: "throughput и свобода по времени",
    hint: "Каждая непустая строка — отдельный prompt. POST сразу вернёт 202, UI начнёт polling.",
    promptLabel: "Prompts — по одному на строку",
    button: "Отправить batch job",
    stages: ["client", "queue", "model", "response"],
    observations: ["POST не держит соединение до конца вычисления.", "Все prompts известны заранее и проходят одним широким tensor batch.", "Job хранится в памяти: после рестарта учебного сервера он исчезнет."],
  },
  dynamic: {
    endpoint: "POST /generate/dynamic",
    title: "Continuous batching",
    summary: "Независимые realtime-запросы на короткое время собираются в общий GPU batch.",
    priority: "баланс latency / throughput",
    hint: "UI одновременно отправит несколько запросов. Смотрите общий batch id и batch size.",
    promptLabel: "Базовый prompt",
    button: "Запустить конкурентно",
    stages: ["client", "queue", "model", "response"],
    observations: ["Каждый клиент отправляет обычный одиночный prompt.", "Future связывает ответ модели с исходным HTTP-запросом.", "Окно ожидания повышает шанс batch > 1, но добавляет queue latency."],
  },
  stream: {
    endpoint: "POST /generate/stream",
    title: "Token streaming",
    summary: "Сервер отдаёт SSE-события по мере декодирования, не ожидая полного текста.",
    priority: "минимальный time to first token",
    hint: "Смотрите, как ответ растёт и сколько chunk-событий пришло до done.",
    promptLabel: "Prompt",
    button: "Запустить stream",
    stages: ["client", "model", "response"],
    observations: ["model.generate() работает в отдельном thread и не блокирует event loop.", "SSE передаёт start, token и done как наблюдаемые события.", "Streaming улучшает воспринимаемую скорость, но сам inference не становится быстрее."],
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
let currentMode = "realtime";
let running = false;

function now() {
  return new Date().toLocaleTimeString("ru-RU", { hour12: false, fractionalSecondDigits: 3 });
}

function log(message, isError = false) {
  const row = document.createElement("p");
  const time = document.createElement("time");
  const text = document.createElement("span");
  time.textContent = now();
  text.textContent = message;
  if (isError) text.className = "error";
  row.append(time, text);
  $("#log").prepend(row);
}

function setMode(mode) {
  if (running) return;
  currentMode = mode;
  const config = modes[mode];
  $$(".mode-button").forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
  $("#endpoint").textContent = config.endpoint;
  $("#mode-title").textContent = config.title;
  $("#mode-summary").textContent = config.summary;
  $("#tradeoff-value").textContent = config.priority;
  $("#prompt-label").textContent = config.promptLabel;
  $("#run span").textContent = config.button;
  $("#form-hint").textContent = config.hint;
  $("#concurrency-control").hidden = mode !== "dynamic";
  $("#observations").replaceChildren(...config.observations.map((item) => {
    const li = document.createElement("li"); li.textContent = item; return li;
  }));
  $$(".stage").forEach((stage) => {
    stage.style.opacity = config.stages.includes(stage.dataset.stage) ? "1" : ".34";
    stage.classList.remove("active", "done");
  });
  $("#trace-state").textContent = "готово к запуску";
  if (mode === "batch" && !$("#prompt").value.includes("\n")) fillExample();
}

function fillExample() {
  const examples = {
    realtime: "Explain why GPU batching improves throughput in simple terms.",
    batch: "Explain FastAPI in one sentence.\nExplain CUDA in one sentence.\nExplain model batching in one sentence.\nExplain throughput in one sentence.",
    dynamic: "Explain continuous batching in one sentence",
    stream: "Write a short explanation of token streaming.",
  };
  $("#prompt").value = examples[currentMode];
}

function resetTrace() {
  $$(".stage").forEach((stage) => stage.classList.remove("active", "done"));
}

function activate(stageName, label) {
  const active = $(".stage.active");
  if (active) { active.classList.remove("active"); active.classList.add("done"); }
  const stage = $(`.stage[data-stage="${stageName}"]`);
  if (stage) stage.classList.add("active");
  $("#trace-state").textContent = label;
}

function finishTrace() {
  const active = $(".stage.active");
  if (active) { active.classList.remove("active"); active.classList.add("done"); }
  $("#trace-state").textContent = "завершено";
}

function setMetrics(total = "—", queue = "—", inference = "—", batch = "—") {
  const values = [total, queue, inference, batch];
  $$("#metrics strong").forEach((node, index) => { node.textContent = values[index]; });
}

function showResults(items) {
  const nodes = items.map((item, index) => {
    const row = document.createElement("div");
    row.className = "result-item";
    const meta = document.createElement("small");
    meta.textContent = items.length > 1 ? `result ${index + 1}` : "model output";
    const text = document.createElement("div");
    text.textContent = item || "[модель не сгенерировала видимый текст]";
    row.append(meta, text);
    return row;
  });
  $("#output").replaceChildren(...nodes);
}

async function postJson(path, body) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
  return payload;
}

async function runRealtime(prompt, maxTokens) {
  activate("client", "HTTP request отправлен");
  log("POST /generate отправлен");
  activate("model", "один model.generate()");
  const result = await postJson("/generate", { prompt, max_new_tokens: maxTokens });
  activate("response", "получен цельный JSON response");
  showResults([result.text]);
  setMetrics(`${result.latency_ms} ms`, `${result.queue_ms} ms`, `${result.inference_ms} ms`, result.batch_size);
  $("#result-caption").textContent = `request ${result.request_id.slice(0, 8)} · один HTTP body`;
  log(`Ответ получен целиком за ${result.latency_ms} ms`);
}

async function runBatch(prompt, maxTokens) {
  const prompts = prompt.split("\n").map((line) => line.trim()).filter(Boolean);
  if (!prompts.length) throw new Error("Добавьте хотя бы один prompt");
  activate("client", `отправляем ${prompts.length} prompts`);
  log(`POST /batch: ${prompts.length} prompts`);
  const accepted = await postJson("/batch", { prompts, max_new_tokens: maxTokens });
  activate("queue", `job ${accepted.job_id.slice(0, 8)} принят с HTTP 202`);
  log(`Job ${accepted.job_id.slice(0, 8)} создан; POST уже завершён`);

  let job;
  do {
    await new Promise((resolve) => setTimeout(resolve, 120));
    const response = await fetch(accepted.status_url);
    job = await response.json();
    if (job.status === "running") activate("model", "worker выполняет один batch generate()");
  } while (["queued", "running"].includes(job.status));

  if (job.status === "failed") throw new Error(job.error || "Batch job failed");
  activate("response", "polling получил completed job");
  showResults(job.results || []);
  setMetrics(job.inference_ms ? `${job.inference_ms} ms` : "—", "async job", job.inference_ms ? `${job.inference_ms} ms` : "—", job.prompt_count);
  $("#result-caption").textContent = `job ${job.job_id.slice(0, 8)} · ${job.status}`;
  log(`Batch job завершён: batch_size=${job.prompt_count}`);
}

async function runDynamic(prompt, maxTokens) {
  const count = Math.max(2, Math.min(16, Number($("#concurrency").value)));
  activate("client", `${count} независимых HTTP requests`);
  log(`Одновременно отправлено ${count} запросов на /generate/dynamic`);
  activate("queue", "batcher собирает совместимые запросы");
  const results = await Promise.all(Array.from({ length: count }, (_, index) => postJson("/generate/dynamic", {
    prompt: `${prompt} [request ${index + 1}]`, max_new_tokens: maxTokens,
  })));
  activate("model", "один или несколько собранных batch уже выполнены");
  activate("response", "каждый Future получил свой результат");
  showResults(results.map((result) => result.text));
  const largestBatch = Math.max(...results.map((result) => result.batch_size));
  const maxLatency = Math.max(...results.map((result) => result.latency_ms));
  const maxQueue = Math.max(...results.map((result) => result.queue_ms));
  const inference = Math.max(...results.map((result) => result.inference_ms));
  setMetrics(`${maxLatency.toFixed(2)} ms`, `${maxQueue.toFixed(2)} ms`, `${inference.toFixed(2)} ms`, largestBatch);
  const batchIds = new Set(results.map((result) => result.batch_id));
  $("#result-caption").textContent = `${count} responses · ${batchIds.size} GPU batch(es)`;
  log(`${count} ответов распределены из ${batchIds.size} batch(es); max batch_size=${largestBatch}`);
  await refreshBatcherStats();
}

function parseSseBlock(block) {
  let event = "message";
  const data = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    if (line.startsWith("data:")) data.push(line.slice(5).trim());
  }
  return { event, data: data.length ? JSON.parse(data.join("\n")) : {} };
}

async function runStream(prompt, maxTokens) {
  activate("client", "streaming POST отправлен");
  log("POST /generate/stream; ожидаем SSE start");
  const response = await fetch("/generate/stream", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt, max_new_tokens: maxTokens }) });
  if (!response.ok || !response.body) throw new Error(`Stream HTTP ${response.status}`);
  activate("model", "модель генерирует в worker thread");
  const textNode = document.createElement("div");
  const cursor = document.createElement("span"); cursor.className = "stream-cursor";
  $("#output").replaceChildren(textNode, cursor);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let firstTokenAt = null;
  let donePayload = null;

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done }).replace(/\r\n/g, "\n");
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      if (!block.trim()) continue;
      const message = parseSseBlock(block);
      if (message.event === "token") {
        if (firstTokenAt === null) { firstTokenAt = message.data.elapsed_ms; activate("response", "первый chunk уже у клиента"); log(`Первый chunk через ${firstTokenAt} ms`); }
        textNode.textContent = message.data.text;
        $("#result-caption").textContent = `${message.data.index} chunk-событий получено`;
      }
      if (message.event === "done") donePayload = message.data;
    }
    if (done) break;
  }
  cursor.remove();
  if (donePayload) {
    setMetrics(`${donePayload.latency_ms} ms`, "—", "stream", 1);
    $("#result-caption").textContent = `${donePayload.chunks} chunks · TTFT ${firstTokenAt ?? "—"} ms`;
    log(`Stream завершён: ${donePayload.chunks} chunks за ${donePayload.latency_ms} ms`);
  }
}

async function run() {
  if (running) return;
  const prompt = $("#prompt").value.trim();
  const maxTokens = Number($("#max-tokens").value);
  if (!prompt) { log("Prompt пуст", true); $("#prompt").focus(); return; }
  running = true;
  $("#run").disabled = true;
  resetTrace();
  setMetrics();
  $("#result-caption").textContent = "выполняется…";
  try {
    if (currentMode === "realtime") await runRealtime(prompt, maxTokens);
    if (currentMode === "batch") await runBatch(prompt, maxTokens);
    if (currentMode === "dynamic") await runDynamic(prompt, maxTokens);
    if (currentMode === "stream") await runStream(prompt, maxTokens);
    finishTrace();
  } catch (error) {
    $("#trace-state").textContent = "ошибка";
    $("#result-caption").textContent = error.message;
    log(error.message, true);
  } finally {
    running = false;
    $("#run").disabled = false;
  }
}

async function refreshBatcherStats() {
  try {
    const response = await fetch("/batcher/stats");
    const stats = await response.json();
    $("#max-batch").textContent = stats.max_batch_size;
    $("#wait-window").textContent = `${stats.max_wait_ms} ms`;
    $("#queue-size").textContent = stats.queue_size;
  } catch (_) { /* health indicator handles connection errors */ }
}

async function health() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    $("#status-dot").className = "status-dot online";
    $("#server-status").textContent = `${data.device.toUpperCase()} · ${data.model}`;
    await refreshBatcherStats();
  } catch (_) {
    $("#status-dot").className = "status-dot error";
    $("#server-status").textContent = "Сервер недоступен";
  }
}

$$(".mode-button").forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));
$("#run").addEventListener("click", run);
$("#fill-example").addEventListener("click", fillExample);
$("#clear-log").addEventListener("click", () => $("#log").replaceChildren());
document.addEventListener("keydown", (event) => { if (event.ctrlKey && event.key === "Enter") run(); });
setMode("realtime");
health();
setInterval(refreshBatcherStats, 2000);
