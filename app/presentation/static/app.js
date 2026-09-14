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
    observations: ["Каждый клиент отправляет обычный одиночный prompt.", "Future связывает ответ модели с исходным HTTP-запросом.", "Окно ожидания повышает шанс batch > 1, но добавляет queue latency.", "Одинаковый prompt и greedy decoding дают одинаковый текст: batching меняет вычисление, а не смысл ответа."],
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

function chips(labels, result = false) {
  const className = result ? "result-chip" : "request-chip";
  return `<div class="${result ? "result-stack" : "request-stack"}">${labels
    .map((label) => `<span class="${className}"><i></i>${label}</span>`)
    .join("")}</div>`;
}

function tensor(rows = 1, columns = 8) {
  const cells = Array.from({ length: rows * columns }, () => "<span></span>").join("");
  return `<div class="tensor ${rows > 1 ? "rows-4" : ""}" aria-hidden="true">${cells}</div>`;
}

function gpuArray() {
  const cells = Array.from({ length: 12 }, (_, index) => `<span>${index % 3 === 1 ? "×" : "·"}</span>`).join("");
  return `<div class="gpu-array" aria-hidden="true">${cells}</div>`;
}

function moduleMarkup(step, label, badge, content, foot, className = "") {
  return `<button class="compute-module ${className}" data-from="${step}" type="button" aria-pressed="false">
    <span class="module-label">${label}<b>${badge}</b></span>
    ${content}
    <span class="module-foot">${foot}</span>
  </button>`;
}

function linkMarkup(step, label) {
  return `<div class="flow-link" data-from="${step}" aria-hidden="true"><small>${label}</small></div>`;
}

function kvCacheMap(withNewToken = false) {
  const tokens = withNewToken ? ["t1", "t2", "t3", "t4", "t5"] : ["t1", "t2", "t3", "t4"];
  const header = tokens.map((token, index) => `<span class="${withNewToken && index === tokens.length - 1 ? "is-new" : ""}">${token}</span>`).join("");
  const rows = ["K·L1", "V·L1", "K·L2", "V·L2"].map((label) => {
    const cells = tokens.map((_, index) => `<i class="${withNewToken && index === tokens.length - 1 ? "is-new" : ""}"></i>`).join("");
    return `<div class="kv-cache-row"><b>${label}</b>${cells}</div>`;
  }).join("");
  return `<div class="kv-cache-map" style="--cache-columns: ${tokens.length}" aria-hidden="true">
    <div class="kv-cache-head"><b>слой</b>${header}</div>
    ${rows}
  </div>`;
}

function qkvProjection() {
  return `<div class="qkv-projection" aria-hidden="true">
    <span><b>Q</b><small>искать</small></span>
    <span><b>K</b><small>записать</small></span>
    <span><b>V</b><small>записать</small></span>
  </div>`;
}

function attentionPath() {
  return `<div class="attention-path" aria-hidden="true">
    <span>Q<sub>new</sub></span><i>×</i><span>K cache</span><i>→</i><span>scores</span><i>×</i><span>V cache</span><i>→</i><span>context</span>
  </div>`;
}

function streamDelivery() {
  return `<div class="stream-delivery" aria-hidden="true">
    <span><b>2841</b><small>token id</small></span>
    <i>→</i>
    <span><b>«кэш»</b><small>decode</small></span>
    <i>→</i>
    <span><b>event: token</b><small>SSE chunk</small></span>
    <i>→</i>
    <span><b>браузер</b><small>append</small></span>
  </div>`;
}

const mechanics = {
  realtime: {
    note: "учебный пример: 4 concurrent requests → 4 model calls",
    kicker: "online realtime · вычислительная схема",
    title: "Запросы проходят GPU по одному",
    summary: "Для сравнения показаны четыре конкурентных HTTP-запроса: каждый отдельно токенизируется, запускает generate() и ждёт полный JSON.",
    aria: "Realtime: четыре независимых запроса превращаются в отдельные узкие тензоры и обрабатываются четырьмя последовательными вызовами модели.",
    steps: [
      ["Независимые HTTP-запросы", "Сервер не ждёт соседние запросы и не объединяет их: каждый клиент создаёт отдельную работу."],
      ["Четыре узкие матрицы", "Tokenizer строит input_ids формы [1 × T] отдельно для каждого prompt."],
      ["Последовательные GPU-вызовы", "Model lock пропускает четыре generate() по очереди. Узкий tensor может использовать вычислительные блоки GPU хуже широкого batch."],
      ["Четыре полных ответа", "Каждый клиент получает один JSON только после завершения своей генерации."],
    ],
    board: () => `<div class="compute-flow">
      ${moduleMarkup(0, "HTTP input", "4 requests", chips(["request 1", "request 2", "request 3", "request 4"]), "независимые клиенты")}
      ${linkMarkup(1, "tokenize")}
      ${moduleMarkup(1, "input_ids", "4 × [1×T]", `<div class="serial-lanes"><i class="serial-lane"></i><i class="serial-lane"></i><i class="serial-lane"></i><i class="serial-lane"></i></div>`, "отдельные tensors")}
      ${linkMarkup(2, "4 calls")}
      ${moduleMarkup(2, "Model / GPU", "batch=1", gpuArray(), "generate() × 4")}
      ${linkMarkup(3, "JSON")}
      ${moduleMarkup(3, "HTTP output", "4 bodies", chips(["response 1", "response 2", "response 3", "response 4"], true), "ответ целиком")}
    </div>`,
  },
  batch: {
    note: "prompts → input_ids [B×T] → activations [B×T×H] → один call",
    kicker: "offline batch · вычислительная схема",
    title: "Много строк становятся одной batch-матрицей",
    summary: "Все prompts известны заранее, поэтому tokenizer собирает их в один tensor и GPU обрабатывает строки совместно.",
    aria: "Offline batch: четыре prompt объединяются в матрицу размера B на T, умножаются на веса модели одним широким GPU-вызовом и разделяются обратно на четыре результата.",
    steps: [
      ["Набор prompts", "Клиент отправляет несколько задач одним offline job и сразу получает job_id."],
      ["Сборка tensor [B × T]", "Tokenizer кодирует строки и дополняет короткие sequences padding-токенами до общей длины T."],
      ["Широкое матричное вычисление", "Embedding переводит IDs в activations [B × T × H]. Линейные и attention-проекции выполняют GEMM над B строками совместно. На GPU это обычно повышает throughput; проверять нужно в prompts/sec, а не обещанием меньшей latency."],
      ["Разделение результатов", "Строка output[i] возвращается соответствующему prompt[i], а клиент забирает готовый job через polling."],
    ],
    board: () => `<div class="compute-flow">
      ${moduleMarkup(0, "Job payload", "B=4", chips(["prompt A", "prompt B", "prompt C", "prompt D"]), "POST → 202 + job_id")}
      ${linkMarkup(1, "pad + stack")}
      ${moduleMarkup(1, "Batch tensor", "[4×T]", tensor(4, 8), "четыре строки input_ids")}
      ${linkMarkup(2, "embed → X · W")}
      ${moduleMarkup(2, "GPU matrix units", "1 call", gpuArray(), "параллельные блоки")}
      ${linkMarkup(3, "split")}
      ${moduleMarkup(3, "Job result", "4 outputs", chips(["output A", "output B", "output C", "output D"], true), "GET /batch/{id}")}
    </div>`,
  },
  dynamic: {
    note: "пример: requests → условные arrivals → runtime wait window → batch",
    kicker: "continuous batching · вычислительная схема",
    title: "Короткое окно собирает realtime-запросы",
    summary: "API остаётся одиночным для каждого клиента, но scheduler объединяет успевшие запросы в один GPU batch. Интервалы arrivals ниже условные.",
    aria: "Continuous batching: независимые запросы приходят в разное время, собираются в коротком окне очереди, образуют общую матрицу и возвращаются исходным клиентам через Future.",
    steps: [
      ["Запросы приходят независимо", "Каждый клиент отправляет обычный одиночный prompt и получает собственный Future."],
      ["Scheduler открывает wait window", "Первый запрос запускает короткое окно. Batcher собирает до max_batch_size совместимых задач."],
      ["Собранный tensor идёт на GPU", "После padding и embedding activations имеют batch-ось N. Prompts одного batch получают общий batch_id и проходят через один generate_batch()."],
      ["Future возвращает правильный output", "Позиция результата сопоставляется с исходной задачей: output[i] завершает future[i]."],
    ],
    board: () => `<div class="compute-flow">
      ${moduleMarkup(0, "HTTP arrivals", "N requests", chips(["request A · 0ms", "request B · +4ms", "request C · +9ms", "request D · +14ms"]), "отдельные соединения")}
      ${linkMarkup(1, "enqueue")}
      ${moduleMarkup(1, "Async queue", "≤20ms", `<div class="queue-window" data-window="wait window"><div class="queue-slots"><i></i><i></i><i></i><i></i></div></div>`, "до max_batch_size")}
      ${linkMarkup(2, "collect")}
      ${moduleMarkup(2, "GPU batch", "[N×T]", tensor(4, 8), "один batch_id")}
      ${linkMarkup(3, "zip futures")}
      ${moduleMarkup(3, "HTTP outputs", "N futures", chips(["A ← output 1", "B ← output 2", "C ← output 3", "D ← output 4"], true), "каждому свой response")}
    </div>`,
  },
  stream: {
    note: "prefill → KV cache → attention read → append → SSE",
    kicker: "token streaming · KV-cache explorer",
    title: "Один decode-шаг без повторного расчёта прошлого",
    summary: "Выберите этап или запустите replay: схема показывает, что хранится в KV-cache, как новый Query читает прошлый контекст и где начинается SSE.",
    aria: "Streaming и KV cache: prompt токенизируется, prefill записывает Keys и Values для всех слоёв, новый Query читает сохранённый контекст, новые Key и Value дописываются в cache, а готовый токен отправляется клиенту как SSE событие.",
    steps: [
      ["Tokenizer строит input_ids", "Prompt входит один раз и превращается в T токенов. Это исходная последовательность, которую модель должна прочитать перед генерацией."],
      ["Prefill заполняет KV-cache", "Все prompt-токены обрабатываются параллельно. На каждом attention-слое модель сохраняет их Key и Value. Query прошлого хранить не нужно: он уже выполнил свою работу."],
      ["Для нового токена считаются Q, K и V", "На decode-шаге модель обрабатывает только последний токен. Q нужен для чтения контекста, а новые K и V понадобятся текущему и следующим шагам."],
      ["Query читает сохранённый контекст", "Q нового токена сравнивается со всеми Keys в cache. Полученные attention-веса смешивают соответствующие Values в один context vector — прошлые K и V заново не вычисляются."],
      ["Новые K и V дописываются", "После шага cache растёт с T до T+1 для каждого слоя. Затем цикл повторяется для следующего токена. Экономия вычислений оплачивается памятью, которая растёт с длиной контекста, числом слоёв и batch size."],
      ["Готовый токен уходит через SSE", "Token id декодируется в текст, TextIteratorStreamer отдаёт chunk, а endpoint отправляет event: token. SSE сокращает время до видимого ответа, но не ускоряет вычисления модели — это делает KV-cache."],
    ],
    routeSteps: { client: 0, model: 1, response: 5 },
    board: () => `<div class="kv-flow">
      ${moduleMarkup(0, "01 · Prompt", "[1×T]", `<div class="token-row"><span class="token">Как</span><span class="token">работает</span><span class="token">KV</span><span class="token">cache</span><span class="token">?</span></div><div class="shape-note">input_ids · T=5</div>`, "tokenize один раз", "kv-module")}
      ${moduleMarkup(1, "02 · Prefill", "write K/V", kvCacheMap(), "K/V для каждого слоя и token", "kv-module")}
      ${moduleMarkup(2, "03 · Decode", "1 token", qkvProjection(), "Q читаем · K/V сохраняем", "kv-module")}
      ${moduleMarkup(3, "04 · Attention", "read cache", attentionPath(), "прошлое не считаем повторно", "kv-module")}
      ${moduleMarkup(4, "05 · Append", "T → T+1", `${kvCacheMap(true)}<div class="decode-loop-note">↻ следующий decode-шаг</div>`, "cache растёт на одну позицию", "kv-module")}
      ${moduleMarkup(5, "06 · Delivery", "SSE", `${streamDelivery()}<div class="token-stream"><span class="stream-token">Ответ</span><span class="stream-token"> растёт</span><span class="stream-token"> сразу</span></div>`, "event: token … event: done", "kv-module")}
    </div>`,
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const examples = {
  realtime: "Объясни простыми словами, зачем нужен batching на GPU.",
  batch: "Объясни FastAPI одним предложением.\nОбъясни CUDA одним предложением.\nОбъясни batching моделей одним предложением.\nОбъясни throughput одним предложением.",
  dynamic: "Объясни, как непрерывный динамический батчинг объединяет запросы. Ответь одним предложением на русском языке.",
  stream: "Коротко объясни, как работает потоковая генерация токенов.",
};
const promptValues = { ...examples };
let currentMode = null;
let running = false;
let mechanicsRunId = 0;
let mechanicsTimer = null;
let mechanicsResolve = null;

function now() {
  const date = new Date();
  const time = [date.getHours(), date.getMinutes(), date.getSeconds()]
    .map((part) => String(part).padStart(2, "0"))
    .join(":");
  return `${time}.${String(date.getMilliseconds()).padStart(3, "0")}`;
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

function cancelMechanicsPlayback() {
  mechanicsRunId += 1;
  if (mechanicsTimer) window.clearTimeout(mechanicsTimer);
  mechanicsTimer = null;
  if (mechanicsResolve) mechanicsResolve(false);
  mechanicsResolve = null;
  $("#mechanics-replay").disabled = false;
}

function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function setMechanicsStep(index) {
  const config = mechanics[currentMode];
  const boundedIndex = Math.max(0, Math.min(config.steps.length - 1, index));
  const board = $("#mechanics-board");
  board.dataset.step = String(boundedIndex);
  board.querySelectorAll("[data-from]").forEach((element) => {
    const elementStep = Number(element.dataset.from);
    element.classList.toggle("is-reached", elementStep <= boundedIndex);
    element.classList.toggle("is-current", elementStep === boundedIndex);
    if (element.matches(".compute-module")) {
      element.setAttribute("aria-pressed", String(elementStep === boundedIndex));
    }
  });
  $("#mechanics-step-number").textContent = `${String(boundedIndex + 1).padStart(2, "0")} / ${String(config.steps.length).padStart(2, "0")}`;
  $("#mechanics-step-title").textContent = config.steps[boundedIndex][0];
  $("#mechanics-step-copy").textContent = config.steps[boundedIndex][1];
}

function renderMechanics(mode) {
  const config = mechanics[mode];
  $("#mechanics-toggle-note").textContent = config.note;
  $("#mechanics-kicker").textContent = config.kicker;
  $("#mechanics-title").textContent = config.title;
  $("#mechanics-summary").textContent = config.summary;
  $("#mechanics-board").setAttribute("aria-label", config.aria);
  $("#mechanics-board").innerHTML = config.board();
  setMechanicsStep(0);
}

function waitForMechanics(duration, runId) {
  return new Promise((resolve) => {
    mechanicsResolve = resolve;
    mechanicsTimer = window.setTimeout(() => {
      mechanicsTimer = null;
      if (mechanicsResolve === resolve) mechanicsResolve = null;
      resolve(runId === mechanicsRunId);
    }, duration);
  });
}

async function playMechanics() {
  cancelMechanicsPlayback();
  if (prefersReducedMotion()) {
    setMechanicsStep(mechanics[currentMode].steps.length - 1);
    return;
  }
  const runId = mechanicsRunId;
  $("#mechanics-replay").disabled = true;
  for (let index = 0; index < mechanics[currentMode].steps.length; index += 1) {
    if (runId !== mechanicsRunId || $("#mechanics-lab").hidden) return;
    setMechanicsStep(index);
    const current = await waitForMechanics(index === 0 ? 850 : 1100, runId);
    if (!current) return;
  }
  if (runId === mechanicsRunId) $("#mechanics-replay").disabled = false;
}

function toggleMechanics() {
  const lab = $("#mechanics-lab");
  const expanded = lab.hidden;
  lab.hidden = !expanded;
  $("#mechanics-toggle").setAttribute("aria-expanded", String(expanded));
  if (expanded) {
    if (prefersReducedMotion()) setMechanicsStep(0);
    else playMechanics();
  } else {
    cancelMechanicsPlayback();
  }
}

function syncMechanicsWithStage(stageName) {
  if ($("#mechanics-lab").hidden) return;
  const stageSteps = mechanics[currentMode].routeSteps || { client: 0, queue: 1, model: 2, response: 3 };
  if (stageName in stageSteps) setMechanicsStep(stageSteps[stageName]);
}

function setMode(mode) {
  if (running) return;
  cancelMechanicsPlayback();
  if (currentMode) promptValues[currentMode] = $("#prompt").value;
  currentMode = mode;
  const config = modes[mode];
  document.documentElement.dataset.mode = mode;
  $$(".mode-button").forEach((button) => {
    const active = button.dataset.mode === mode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  $("#endpoint").textContent = config.endpoint;
  $("#mode-title").textContent = config.title;
  $("#mode-summary").textContent = config.summary;
  $("#tradeoff-value").textContent = config.priority;
  $("#prompt-label").textContent = config.promptLabel;
  $("#run-label").textContent = config.button;
  $("#form-hint").textContent = config.hint;
  $("#concurrency-control").hidden = mode !== "dynamic";
  $("#prompt").value = promptValues[mode];
  $("#pipeline").dataset.flowCount = ["batch", "dynamic"].includes(mode) ? "4" : "1";
  $("#observations").replaceChildren(...config.observations.map((item) => {
    const li = document.createElement("li"); li.textContent = item; return li;
  }));
  $$(".stage").forEach((stage) => {
    stage.style.opacity = config.stages.includes(stage.dataset.stage) ? "1" : ".34";
    stage.classList.remove("active", "done");
  });
  $("#trace-state").textContent = "готово к запуску";
  renderMechanics(mode);
  if (!$("#mechanics-lab").hidden && !prefersReducedMotion()) playMechanics();
}

function fillExample() {
  promptValues[currentMode] = examples[currentMode];
  $("#prompt").value = examples[currentMode];
}

function resetTrace() {
  $$(".stage").forEach((stage) => stage.classList.remove("active", "done"));
  $("#pipeline").setAttribute("aria-busy", "true");
  $("#pipeline").style.setProperty("--route-position", "2%");
  cancelMechanicsPlayback();
  if (!$("#mechanics-lab").hidden) setMechanicsStep(0);
}

function activate(stageName, label) {
  const active = $(".stage.active");
  if (active) { active.classList.remove("active"); active.classList.add("done"); }
  const stage = $(`.stage[data-stage="${stageName}"]`);
  if (stage) stage.classList.add("active");
  const routePositions = { client: "2%", queue: "34%", model: "66%", response: "98%" };
  $("#pipeline").style.setProperty("--route-position", routePositions[stageName] || "2%");
  $("#trace-state").textContent = label;
  syncMechanicsWithStage(stageName);
}

function nextPaint() {
  return new Promise((resolve) => window.requestAnimationFrame(() => window.requestAnimationFrame(resolve)));
}

function finishTrace() {
  const active = $(".stage.active");
  if (active) { active.classList.remove("active"); active.classList.add("done"); }
  $("#trace-state").textContent = "завершено";
  $("#pipeline").setAttribute("aria-busy", "false");
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
  await nextPaint();
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
  const pendingResults = Promise.all(Array.from({ length: count }, () => postJson("/generate/dynamic", {
    prompt, max_new_tokens: maxTokens,
  })));
  const results = await pendingResults;
  activate("model", "один или несколько собранных batch уже выполнены");
  await nextPaint();
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
  const visualCount = currentMode === "batch"
    ? prompt.split("\n").map((line) => line.trim()).filter(Boolean).length
    : currentMode === "dynamic"
      ? Number($("#concurrency").value)
      : 1;
  $("#pipeline").dataset.flowCount = String(Math.max(1, Math.min(4, visualCount)));
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
    $("#pipeline").setAttribute("aria-busy", "false");
    $("#result-caption").textContent = error.message;
    log(error.message, true);
  } finally {
    running = false;
    $("#run").disabled = false;
    promptValues[currentMode] = $("#prompt").value;
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
    $("#mechanics-runtime-note").textContent = data.device === "cuda"
      ? `Активный runtime: ${data.gpu || "CUDA GPU"}. Схема и telemetry относятся к этому ускорителю.`
      : "Активный runtime: CPU. GPU-блоки объясняют CUDA-механику; текущие миллисекунды измерены на CPU.";
    await refreshBatcherStats();
  } catch (_) {
    $("#status-dot").className = "status-dot error";
    $("#server-status").textContent = "Сервер недоступен";
    $("#mechanics-runtime-note").textContent = "Runtime недоступен: запустите сервер и повторите проверку.";
  }
}

$$(".mode-button").forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));
$("#run").addEventListener("click", run);
$("#fill-example").addEventListener("click", fillExample);
$("#mechanics-toggle").addEventListener("click", toggleMechanics);
$("#mechanics-replay").addEventListener("click", playMechanics);
$("#mechanics-board").addEventListener("click", (event) => {
  const selectedStep = event.target.closest(".compute-module");
  if (!selectedStep) return;
  cancelMechanicsPlayback();
  setMechanicsStep(Number(selectedStep.dataset.from));
});
$("#clear-log").addEventListener("click", () => $("#log").replaceChildren());
document.addEventListener("visibilitychange", () => {
  if (document.hidden) cancelMechanicsPlayback();
});
document.addEventListener("keydown", (event) => { if (event.ctrlKey && event.key === "Enter") run(); });
setMode("realtime");
health();
setInterval(refreshBatcherStats, 2000);
