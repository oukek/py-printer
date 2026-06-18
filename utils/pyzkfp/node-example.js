const { spawn } = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const readline = require("node:readline");

const rootDir = path.resolve(__dirname, "..");
const bridgeScript = path.join(rootDir, "tools", "pyzkfp_bridge.py");
const defaultPython = path.join(rootDir, ".venv", "Scripts", "python.exe");
const dataFile = path.join(__dirname, "fingerprint-data.json");

const pythonCmd = process.env.PYTHON || defaultPython;
const deviceIndex = Number.parseInt(process.env.FP_DEVICE_INDEX || "0", 10);
const timeoutMs = Number.parseInt(process.env.FP_TIMEOUT_MS || "15000", 10);
const preferredPort = Number.parseInt(process.env.PORT || "3078", 10);
const logFile = process.env.ATTENDANCE_LOG_FILE || "";

function now() {
  return new Date().toISOString();
}

function log(message, data) {
  const line = data === undefined
    ? `[${now()}] ${message}`
    : `[${now()}] ${message} ${JSON.stringify(data)}`;

  if (logFile) {
    fs.appendFileSync(logFile, `${line}\n`, "utf8");
    return;
  }

  if (data === undefined) {
    try {
      console.log(line);
    } catch (_) {
      // Background launches can close stdout before the process exits.
    }
    return;
  }
  try {
    console.log(line);
  } catch (_) {
    // Background launches can close stdout before the process exits.
  }
}

function defaultStore() {
  return {
    nextFid: 1,
    users: [],
    attendance: [],
  };
}

function readStore() {
  if (!fs.existsSync(dataFile)) {
    return defaultStore();
  }

  const store = JSON.parse(fs.readFileSync(dataFile, "utf8"));
  return {
    ...defaultStore(),
    ...store,
    users: Array.isArray(store.users) ? store.users : [],
    attendance: Array.isArray(store.attendance) ? store.attendance : [],
  };
}

function writeStore(store) {
  const tmpFile = `${dataFile}.tmp`;
  fs.writeFileSync(tmpFile, `${JSON.stringify(store, null, 2)}\n`, "utf8");
  fs.renameSync(tmpFile, dataFile);
}

function publicUser(user) {
  const { templateBase64, ...rest } = user;
  return rest;
}

function publicStore(store) {
  return {
    users: store.users.map(publicUser),
    attendance: store.attendance.slice(-100).reverse(),
  };
}

class FingerprintBridge {
  constructor() {
    this.seq = 0;
    this.pending = new Map();
    this.queue = Promise.resolve();
    this.child = spawn(pythonCmd, [bridgeScript, "--stdio", "--debug"], {
      cwd: rootDir,
      stdio: ["pipe", "pipe", "pipe"],
      windowsHide: true,
    });

    this.child.on("spawn", () => {
      log("Python bridge started", {
        command: pythonCmd,
        script: bridgeScript,
        pid: this.child.pid,
      });
    });

    this.child.on("error", (error) => {
      log("Failed to start Python bridge", {
        name: error.name,
        message: error.message,
      });
    });

    this.child.on("exit", (code, signal) => {
      log("Python bridge exited", { code, signal });
      for (const { reject } of this.pending.values()) {
        reject(new Error(`Python bridge exited before responding: code=${code}, signal=${signal}`));
      }
      this.pending.clear();
    });

    readline.createInterface({ input: this.child.stdout }).on("line", (line) => {
      let message;
      try {
        message = JSON.parse(line);
      } catch (_) {
        log("SDK output", line);
        return;
      }

      const callbacks = this.pending.get(message.id);
      if (!callbacks) return;

      this.pending.delete(message.id);
      if (message.ok) {
        callbacks.resolve(message.result);
        return;
      }

      const bridgeError = new Error(message.error?.message || "Python bridge command failed");
      Object.assign(bridgeError, message.error);
      callbacks.reject(bridgeError);
    });

    this.child.stderr.on("data", (chunk) => {
      const line = `[${now()}] PY STDERR ${chunk}`;
      if (logFile) {
        fs.appendFileSync(logFile, line, "utf8");
        return;
      }
      try {
        process.stderr.write(line);
      } catch (_) {
        // Background launches can close stderr before the process exits.
      }
    });
  }

  call(command, params = {}) {
    if (!this.child.stdin.writable) {
      return Promise.reject(new Error("Python bridge stdin is not writable"));
    }

    const id = String(++this.seq);
    const request = { id, command, params };
    log("NODE -> PY", { command, params });

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.child.stdin.write(`${JSON.stringify(request)}\n`, (error) => {
        if (!error) return;
        this.pending.delete(id);
        reject(error);
      });
    });
  }

  runExclusive(task) {
    const next = this.queue.then(task, task);
    this.queue = next.catch(() => {});
    return next;
  }

  async shutdown() {
    try {
      if (this.child.stdin.writable) {
        await this.call("shutdown");
      }
    } catch (error) {
      log("Shutdown command failed", error.message);
    } finally {
      this.child.stdin.end();
    }
  }
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 1024 * 1024) {
        reject(new Error("Request body is too large"));
        req.destroy();
      }
    });
    req.on("end", () => {
      if (!body) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(body));
      } catch (error) {
        reject(error);
      }
    });
  });
}

function sendJson(res, status, payload) {
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  res.end(JSON.stringify(payload));
}

function sendHtml(res) {
  res.writeHead(200, {
    "content-type": "text/html; charset=utf-8",
    "cache-control": "no-store",
  });
  res.end(html);
}

function sendEvent(res, event, payload) {
  res.write(`event: ${event}\n`);
  res.write(`data: ${JSON.stringify(payload)}\n\n`);
}

function routeParam(url, prefix) {
  if (!url.startsWith(prefix)) return null;
  const value = decodeURIComponent(url.slice(prefix.length).split("?")[0]);
  return value || null;
}

async function startBridge() {
  const bridge = new FingerprintBridge();
  const store = readStore();

  await bridge.call("ping");
  const devices = await bridge.call("device_count");
  if (!devices.count) {
    throw new Error("No fingerprint device found.");
  }

  const opened = await bridge.call("open", { index: deviceIndex });
  log("Fingerprint device opened", opened);

  let loaded = 0;
  for (const user of store.users) {
    if (!user.templateBase64) continue;
    await bridge.call("add_template", {
      fid: user.fid,
      templateBase64: user.templateBase64,
    });
    loaded += 1;
  }
  log("Templates loaded", { count: loaded });

  return bridge;
}

function createServer(bridge) {
  return http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, "http://localhost");

      if (req.method === "GET" && url.pathname === "/") {
        sendHtml(res);
        return;
      }

      if (req.method === "GET" && url.pathname === "/api/state") {
        sendJson(res, 200, publicStore(readStore()));
        return;
      }

      if (req.method === "GET" && url.pathname === "/api/enroll-events") {
        const name = String(url.searchParams.get("name") || "").trim();
        const employeeNo = String(url.searchParams.get("employeeNo") || "").trim();
        if (!name) {
          sendJson(res, 400, { error: "Name is required" });
          return;
        }

        res.writeHead(200, {
          "content-type": "text/event-stream; charset=utf-8",
          "cache-control": "no-store",
          connection: "keep-alive",
        });

        await bridge.runExclusive(async () => {
          const store = readStore();
          const fid = store.nextFid || 1;
          const captures = [];
          const templates = [];

          sendEvent(res, "progress", {
            step: 0,
            total: 3,
            message: "开始录入，请准备按压同一根手指",
          });

          for (let index = 0; index < 3; index += 1) {
            sendEvent(res, "progress", {
              step: index + 1,
              total: 3,
              message: `等待第 ${index + 1} 次按压`,
            });

            const capture = await bridge.call("capture", { timeoutMs });
            const templateBase64 = capture.templateBase64;

            if (templates.length) {
              const matched = await bridge.call("match", {
                template1Base64: templates[templates.length - 1],
                template2Base64: templateBase64,
              });
              if (matched.score <= 0) {
                await bridge.call("light", { color: "red", duration: 0.9 });
                throw new Error("检测到不同手指，请重新录入同一根手指。");
              }
            }

            templates.push(templateBase64);
            captures.push(capture);
            await bridge.call("light", { color: "green", duration: 0.25 });

            sendEvent(res, "captured", {
              step: index + 1,
              total: 3,
              message: `第 ${index + 1} 次采集成功，请抬起手指`,
              capture: {
                width: capture.width,
                height: capture.height,
                imageBase64: capture.imageBase64,
              },
            });
          }

          sendEvent(res, "progress", {
            step: 3,
            total: 3,
            message: "正在合并模板并保存用户",
          });

          const merged = await bridge.call("merge_templates", {
            fid,
            templatesBase64: templates,
          });

          const user = {
            fid,
            name,
            employeeNo,
            templateBase64: merged.templateBase64,
            templateLength: merged.templateLength,
            imageWidth: captures[0]?.width || null,
            imageHeight: captures[0]?.height || null,
            createdAt: now(),
            updatedAt: now(),
          };

          store.nextFid = fid + 1;
          store.users.push(user);
          writeStore(store);

          await bridge.call("light", { color: "green", duration: 0.7 });
          sendEvent(res, "done", {
            user: publicUser(user),
            message: `录入成功：${user.name} / FID ${user.fid}`,
          });
        }).catch((error) => {
          sendEvent(res, "failed", {
            error: error.message,
            type: error.type || error.name,
            traceback: error.traceback,
          });
        });

        res.end();
        return;
      }

      if (req.method === "POST" && url.pathname === "/api/enroll") {
        const body = await parseBody(req);
        const name = String(body.name || "").trim();
        const employeeNo = String(body.employeeNo || "").trim();
        if (!name) {
          sendJson(res, 400, { error: "Name is required" });
          return;
        }

        const result = await bridge.runExclusive(async () => {
          const store = readStore();
          const fid = store.nextFid || 1;
          await bridge.call("light", { color: "green", duration: 0.2 });
          const enrolled = await bridge.call("enroll", {
            fid,
            timeoutMs: Number.parseInt(body.timeoutMs || timeoutMs, 10),
          });

          const user = {
            fid,
            name,
            employeeNo,
            templateBase64: enrolled.templateBase64,
            templateLength: enrolled.templateLength,
            imageWidth: enrolled.captures[0]?.width || null,
            imageHeight: enrolled.captures[0]?.height || null,
            createdAt: now(),
            updatedAt: now(),
          };

          store.nextFid = fid + 1;
          store.users.push(user);
          writeStore(store);

          await bridge.call("light", { color: "green", duration: 0.7 });
          return {
            user: publicUser(user),
            captures: enrolled.captures.map((capture) => ({
              width: capture.width,
              height: capture.height,
              imageBase64: capture.imageBase64,
            })),
          };
        });

        sendJson(res, 200, result);
        return;
      }

      if (req.method === "POST" && url.pathname === "/api/identify") {
        const body = await parseBody(req);
        const result = await bridge.runExclusive(async () => {
          const identified = await bridge.call("identify", {
            timeoutMs: Number.parseInt(body.timeoutMs || timeoutMs, 10),
          });

          const store = readStore();
          const user = store.users.find((item) => item.fid === identified.fid) || null;
          const minIntervalMs = Number.parseInt(body.minIntervalMs || "0", 10);
          const recordUnmatched = body.recordUnmatched !== false;
          const lastRecord = store.attendance[store.attendance.length - 1];
          const duplicate = Boolean(
            user &&
            minIntervalMs > 0 &&
            lastRecord &&
            lastRecord.fid === user.fid &&
            Date.now() - new Date(lastRecord.createdAt).getTime() < minIntervalMs
          );
          const event = {
            id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
            fid: identified.fid || null,
            name: user?.name || null,
            employeeNo: user?.employeeNo || null,
            score: identified.score,
            matched: Boolean(user),
            duplicate,
            createdAt: now(),
          };

          if (!duplicate && (user || recordUnmatched)) {
            store.attendance.push(event);
            writeStore(store);
          }

          await bridge.call("light", {
            color: user ? "green" : "red",
            duration: user ? 0.5 : 0.9,
          });

          return {
            event,
            user: user ? publicUser(user) : null,
            recorded: !duplicate && (Boolean(user) || recordUnmatched),
            capture: identified.capture
              ? {
                  width: identified.capture.width,
                  height: identified.capture.height,
                  imageBase64: identified.capture.imageBase64,
                }
              : null,
          };
        });

        sendJson(res, 200, result);
        return;
      }

      const deleteFid = routeParam(url.pathname, "/api/users/");
      if (req.method === "DELETE" && deleteFid) {
        const fid = Number.parseInt(deleteFid, 10);
        if (!Number.isInteger(fid)) {
          sendJson(res, 400, { error: "Invalid fid" });
          return;
        }

        const result = await bridge.runExclusive(async () => {
          const store = readStore();
          const userIndex = store.users.findIndex((item) => item.fid === fid);
          if (userIndex < 0) {
            sendJson(res, 404, { error: "User not found" });
            return null;
          }

          await bridge.call("delete_template", { fid });
          const [removed] = store.users.splice(userIndex, 1);
          writeStore(store);
          return { removed: publicUser(removed) };
        });

        if (result) sendJson(res, 200, result);
        return;
      }

      if (req.method === "DELETE" && url.pathname === "/api/attendance") {
        const store = readStore();
        store.attendance = [];
        writeStore(store);
        sendJson(res, 200, { cleared: true });
        return;
      }

      sendJson(res, 404, { error: "Not found" });
    } catch (error) {
      log("Request failed", {
        name: error.name,
        message: error.message,
        traceback: error.traceback,
      });
      sendJson(res, 500, {
        error: error.message,
        type: error.type || error.name,
        traceback: error.traceback,
      });
    }
  });
}

function listen(server, port) {
  return new Promise((resolve, reject) => {
    server.once("error", (error) => {
      if (error.code === "EADDRINUSE" && port < preferredPort + 20) {
        resolve(listen(server, port + 1));
        return;
      }
      reject(error);
    });

    server.listen(port, "127.0.0.1", () => {
      resolve(port);
    });
  });
}

const html = String.raw`<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>指纹考勤测试台</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #18202b;
      --muted: #647084;
      --line: #d9dee7;
      --blue: #1f6feb;
      --green: #17803d;
      --red: #c7352f;
      --amber: #9a6700;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      font-size: 14px;
    }
    header {
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 650;
      letter-spacing: 0;
    }
    main {
      display: grid;
      grid-template-columns: minmax(280px, 360px) 1fr;
      gap: 16px;
      padding: 16px;
      max-width: 1280px;
      margin: 0 auto;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 0;
    }
    .section-head {
      min-height: 48px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 14px;
      border-bottom: 1px solid var(--line);
      gap: 10px;
    }
    h2 {
      margin: 0;
      font-size: 15px;
      font-weight: 650;
      letter-spacing: 0;
    }
    .stack { display: grid; gap: 12px; padding: 14px; }
    label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 12px;
    }
    input {
      height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 10px;
      color: var(--ink);
      font: inherit;
      background: #fff;
    }
    button {
      height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 12px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      cursor: pointer;
      white-space: nowrap;
    }
    button.primary {
      border-color: var(--blue);
      background: var(--blue);
      color: #fff;
      font-weight: 600;
    }
    button.danger {
      border-color: #f0b8b5;
      color: var(--red);
    }
    button:disabled {
      opacity: .55;
      cursor: wait;
    }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .status {
      min-height: 34px;
      padding: 8px 10px;
      border-radius: 6px;
      background: #eef2f8;
      color: var(--muted);
      overflow-wrap: anywhere;
    }
    .status.ok { background: #e8f5ee; color: var(--green); }
    .status.err { background: #fdeceb; color: var(--red); }
    .status.live { background: #eaf2ff; color: var(--blue); }
    .progress {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }
    .progress-step {
      height: 34px;
      display: grid;
      place-items: center;
      border: 1px solid var(--line);
      border-radius: 6px;
      color: var(--muted);
      background: #fafbfc;
      font-weight: 600;
    }
    .progress-step.active {
      border-color: #9dc0ff;
      background: #eaf2ff;
      color: var(--blue);
    }
    .progress-step.done {
      border-color: #8fd3a7;
      background: #e8f5ee;
      color: var(--green);
    }
    .toast {
      position: fixed;
      top: 72px;
      right: 18px;
      z-index: 20;
      min-width: 260px;
      max-width: min(420px, calc(100vw - 32px));
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-left: 5px solid var(--blue);
      border-radius: 8px;
      background: #fff;
      box-shadow: 0 16px 40px rgba(21, 32, 50, .18);
      transform: translateY(-10px);
      opacity: 0;
      pointer-events: none;
      transition: opacity .18s ease, transform .18s ease;
    }
    .toast.show {
      transform: translateY(0);
      opacity: 1;
    }
    .toast.ok { border-left-color: var(--green); }
    .toast.err { border-left-color: var(--red); }
    .toast strong {
      display: block;
      margin-bottom: 4px;
      font-size: 16px;
    }
    .toast span {
      color: var(--muted);
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th, td {
      text-align: left;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      vertical-align: middle;
    }
    th {
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
      background: #fafbfc;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    .result {
      min-height: 96px;
      display: grid;
      align-content: center;
      gap: 6px;
      padding: 14px;
      border-bottom: 1px solid var(--line);
    }
    .result strong { font-size: 22px; letter-spacing: 0; }
    .muted { color: var(--muted); }
    canvas {
      width: 100%;
      max-width: 300px;
      aspect-ratio: 3 / 4;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #eef0f4;
      image-rendering: pixelated;
    }
    .preview {
      display: flex;
      align-items: flex-start;
      gap: 14px;
      padding: 14px;
      flex-wrap: wrap;
    }
    .empty {
      padding: 16px;
      color: var(--muted);
    }
    @media (max-width: 900px) {
      main { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
      header { align-items: flex-start; height: auto; padding: 14px 16px; gap: 8px; flex-direction: column; }
    }
  </style>
</head>
<body>
  <div class="toast" id="toast"><strong></strong><span></span></div>
  <header>
    <h1>指纹考勤测试台</h1>
    <div class="muted" id="clock"></div>
  </header>

  <main>
    <section>
      <div class="section-head"><h2>操作</h2></div>
      <div class="stack">
        <label>姓名<input id="name" autocomplete="off" /></label>
        <label>工号<input id="employeeNo" autocomplete="off" /></label>
        <div class="actions">
          <button class="primary" id="enrollBtn">录入指纹</button>
          <button id="identifyBtn">暂停识别</button>
        </div>
        <div class="progress" id="enrollProgress">
          <div class="progress-step">1</div>
          <div class="progress-step">2</div>
          <div class="progress-step">3</div>
        </div>
        <div class="status" id="status">设备已连接</div>
      </div>
    </section>

    <section>
      <div class="section-head"><h2>识别结果</h2></div>
      <div class="result" id="result">
        <strong>等待操作</strong>
        <span class="muted">最近一次识别会显示在这里</span>
      </div>
      <div class="preview">
        <canvas id="fingerCanvas" width="300" height="400"></canvas>
        <div class="muted" id="imageMeta">暂无图像</div>
      </div>
    </section>

    <section>
      <div class="section-head"><h2>用户指纹</h2><span class="muted" id="userCount">0 人</span></div>
      <div id="users"></div>
    </section>

    <section>
      <div class="section-head">
        <h2>考勤记录</h2>
        <button class="danger" id="clearAttendanceBtn">清空记录</button>
      </div>
      <div id="attendance"></div>
    </section>
  </main>

  <script>
    const state = {
      busy: false,
      autoIdentify: true,
      identifying: false,
      enrolling: false,
      autoTimer: null,
    };
    const el = (id) => document.getElementById(id);

    function setBusy(busy) {
      state.busy = busy;
      document.querySelectorAll("button").forEach((button) => {
        button.disabled = busy;
      });
    }

    function updateIdentifyButton() {
      el("identifyBtn").textContent = state.autoIdentify ? "暂停识别" : "继续识别";
    }

    function setStatus(text, type = "") {
      const node = el("status");
      node.textContent = text;
      node.className = "status" + (type ? " " + type : "");
    }

    function showToast(title, detail = "", type = "") {
      const toast = el("toast");
      toast.querySelector("strong").textContent = title;
      toast.querySelector("span").textContent = detail;
      toast.className = "toast show" + (type ? " " + type : "");
      clearTimeout(showToast.timer);
      showToast.timer = setTimeout(() => {
        toast.className = "toast" + (type ? " " + type : "");
      }, 2600);
    }

    function setEnrollProgress(step, done = false) {
      document.querySelectorAll("#enrollProgress .progress-step").forEach((node, index) => {
        const current = index + 1;
        node.className = "progress-step";
        if (done && current <= step) {
          node.classList.add("done");
        } else if (current < step) {
          node.classList.add("done");
        } else if (current === step) {
          node.classList.add("active");
        }
      });
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        ...options,
        headers: {
          "content-type": "application/json",
          ...(options.headers || {}),
        },
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "请求失败");
      }
      return data;
    }

    function renderImage(capture) {
      const canvas = el("fingerCanvas");
      const meta = el("imageMeta");
      if (!capture || !capture.imageBase64) {
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        meta.textContent = "暂无图像";
        return;
      }

      canvas.width = capture.width;
      canvas.height = capture.height;
      const bytes = Uint8Array.from(atob(capture.imageBase64), (char) => char.charCodeAt(0));
      const image = new ImageData(capture.width, capture.height);
      for (let i = 0; i < bytes.length; i += 1) {
        const offset = i * 4;
        const value = bytes[i];
        image.data[offset] = value;
        image.data[offset + 1] = value;
        image.data[offset + 2] = value;
        image.data[offset + 3] = 255;
      }
      canvas.getContext("2d").putImageData(image, 0, 0);
      meta.textContent = capture.width + " x " + capture.height;
    }

    function renderUsers(users) {
      el("userCount").textContent = users.length + " 人";
      if (!users.length) {
        el("users").innerHTML = '<div class="empty">暂无用户</div>';
        return;
      }

      el("users").innerHTML = '<table><thead><tr><th>FID</th><th>姓名</th><th>工号</th><th>录入时间</th><th></th></tr></thead><tbody>' +
        users.map((user) => '<tr>' +
          '<td>' + user.fid + '</td>' +
          '<td>' + escapeHtml(user.name) + '</td>' +
          '<td>' + escapeHtml(user.employeeNo || "") + '</td>' +
          '<td>' + formatTime(user.createdAt) + '</td>' +
          '<td><button class="danger" data-delete="' + user.fid + '">删除</button></td>' +
        '</tr>').join("") +
        '</tbody></table>';
    }

    function renderAttendance(records) {
      if (!records.length) {
        el("attendance").innerHTML = '<div class="empty">暂无记录</div>';
        return;
      }

      el("attendance").innerHTML = '<table><thead><tr><th>时间</th><th>姓名</th><th>工号</th><th>FID</th><th>分数</th></tr></thead><tbody>' +
        records.map((record) => '<tr>' +
          '<td>' + formatTime(record.createdAt) + '</td>' +
          '<td>' + escapeHtml(record.name || "未匹配") + '</td>' +
          '<td>' + escapeHtml(record.employeeNo || "") + '</td>' +
          '<td>' + (record.fid || "") + '</td>' +
          '<td>' + record.score + '</td>' +
        '</tr>').join("") +
        '</tbody></table>';
    }

    async function refresh() {
      const data = await api("/api/state");
      renderUsers(data.users);
      renderAttendance(data.attendance);
    }

    function scheduleAutoIdentify(delay = 350) {
      clearTimeout(state.autoTimer);
      if (!state.autoIdentify || state.enrolling || state.busy) return;
      state.autoTimer = setTimeout(() => {
        identify({ auto: true }).catch(() => {});
      }, delay);
    }

    async function enroll() {
      const name = el("name").value.trim();
      const employeeNo = el("employeeNo").value.trim();
      if (!name) {
        setStatus("请输入姓名", "err");
        showToast("缺少姓名", "录入前先填写姓名", "err");
        return;
      }

      const resumeAuto = state.autoIdentify;
      state.enrolling = true;
      state.autoIdentify = false;
      clearTimeout(state.autoTimer);
      updateIdentifyButton();
      setBusy(true);
      setEnrollProgress(1);
      setStatus("录入中：等待第 1 次按压");
      showToast("开始录入", "同一根手指按 3 次，每次成功后抬起再按");

      const params = new URLSearchParams({ name, employeeNo });
      const source = new EventSource("/api/enroll-events?" + params.toString());

      source.addEventListener("progress", (event) => {
        const data = JSON.parse(event.data);
        setEnrollProgress(Math.max(data.step, 1));
        setStatus(data.message);
      });

      source.addEventListener("captured", (event) => {
        const data = JSON.parse(event.data);
        setEnrollProgress(data.step, true);
        renderImage(data.capture);
        setStatus(data.message, "ok");
        showToast("第 " + data.step + " 次采集成功", data.step < 3 ? "请抬起手指，准备下一次" : "三次采集完成，正在保存", "ok");
      });

      source.addEventListener("done", async (event) => {
        const data = JSON.parse(event.data);
        source.close();
        setEnrollProgress(3, true);
        setStatus(data.message, "ok");
        showToast("录入成功", data.user.name + " / FID " + data.user.fid, "ok");
        el("name").value = "";
        el("employeeNo").value = "";
        await refresh();
        state.enrolling = false;
        state.autoIdentify = resumeAuto;
        updateIdentifyButton();
        setBusy(false);
        scheduleAutoIdentify(900);
      });

      source.addEventListener("failed", (event) => {
        const data = JSON.parse(event.data);
        source.close();
        setStatus(data.error, "err");
        showToast("录入失败", data.error, "err");
        state.enrolling = false;
        state.autoIdentify = resumeAuto;
        updateIdentifyButton();
        setBusy(false);
        scheduleAutoIdentify(900);
      });

      source.onerror = () => {
        source.close();
        setStatus("录入连接中断，请重试", "err");
        showToast("录入中断", "请重新点击录入指纹", "err");
        state.enrolling = false;
        state.autoIdentify = resumeAuto;
        updateIdentifyButton();
        setBusy(false);
        scheduleAutoIdentify(900);
      };
    }

    async function oldEnroll() {
      const name = el("name").value.trim();
      const employeeNo = el("employeeNo").value.trim();
      if (!name) {
        setStatus("请输入姓名", "err");
        return;
      }

      setBusy(true);
      setStatus("录入中：同一根手指按 3 次，每次成功后抬起再按");
      try {
        const data = await api("/api/enroll", {
          method: "POST",
          body: JSON.stringify({ name, employeeNo }),
        });
        renderImage(data.captures[data.captures.length - 1]);
        setStatus("录入成功：" + data.user.name + " / FID " + data.user.fid, "ok");
        el("name").value = "";
        el("employeeNo").value = "";
        await refresh();
      } catch (error) {
        setStatus(error.message, "err");
      } finally {
        setBusy(false);
      }
    }

    async function identify(options = {}) {
      const auto = Boolean(options.auto);
      if (state.identifying || state.enrolling) return;

      state.identifying = true;
      if (!auto) setBusy(true);
      if (auto) {
        setStatus("自动识别中：请直接按压手指", "live");
      } else {
        setStatus("等待按压手指");
      }
      try {
        const data = await api("/api/identify", {
          method: "POST",
          body: JSON.stringify(auto ? {
            timeoutMs: 2500,
            minIntervalMs: 8000,
            recordUnmatched: false,
          } : {}),
        });
        renderImage(data.capture);
        if (data.user) {
          el("result").innerHTML = '<strong>' + escapeHtml(data.user.name) + '</strong><span class="muted">FID ' + data.user.fid + '，分数 ' + data.event.score + '</span>';
          if (data.event.duplicate) {
            setStatus("已识别：" + data.user.name + "，短时间内不重复打卡", "live");
          } else {
            setStatus("打卡成功：" + data.user.name, "ok");
            showToast("识别成功", data.user.name + " / 分数 " + data.event.score, "ok");
          }
        } else {
          el("result").innerHTML = '<strong>未匹配</strong><span class="muted">分数 ' + data.event.score + '</span>';
          setStatus("未匹配到用户", "err");
          if (!auto) showToast("未匹配", "请确认手指已录入", "err");
        }
        if (!auto || data.recorded) await refresh();
      } catch (error) {
        if (auto && /Timed out waiting for fingerprint capture/i.test(error.message)) {
          setStatus("自动识别中：请直接按压手指", "live");
        } else {
          setStatus(error.message, "err");
          if (!auto) showToast("识别失败", error.message, "err");
        }
      } finally {
        state.identifying = false;
        if (!auto) setBusy(false);
        if (auto) scheduleAutoIdentify(350);
      }
    }

    function toggleAutoIdentify() {
      state.autoIdentify = !state.autoIdentify;
      updateIdentifyButton();
      if (state.autoIdentify) {
        setStatus("自动识别中：请直接按压手指", "live");
        scheduleAutoIdentify(100);
      } else {
        clearTimeout(state.autoTimer);
        setStatus("自动识别已暂停");
      }
    }

    async function deleteUser(fid) {
      if (!confirm("删除 FID " + fid + " 的指纹用户？")) return;
      setBusy(true);
      setStatus("正在删除 FID " + fid);
      try {
        await api("/api/users/" + fid, { method: "DELETE" });
        setStatus("已删除 FID " + fid, "ok");
        await refresh();
      } catch (error) {
        setStatus(error.message, "err");
      } finally {
        setBusy(false);
        scheduleAutoIdentify(500);
      }
    }

    async function clearAttendance() {
      if (!confirm("清空考勤记录？")) return;
      clearTimeout(state.autoTimer);
      setBusy(true);
      try {
        await api("/api/attendance", { method: "DELETE" });
        await refresh();
      } catch (error) {
        setStatus(error.message, "err");
      } finally {
        setBusy(false);
        scheduleAutoIdentify(500);
      }
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[char]));
    }

    function formatTime(value) {
      if (!value) return "";
      return new Date(value).toLocaleString();
    }

    el("enrollBtn").addEventListener("click", enroll);
    el("identifyBtn").addEventListener("click", toggleAutoIdentify);
    el("clearAttendanceBtn").addEventListener("click", clearAttendance);
    el("users").addEventListener("click", (event) => {
      const fid = event.target.getAttribute("data-delete");
      if (fid) deleteUser(fid);
    });
    setInterval(() => {
      el("clock").textContent = new Date().toLocaleString();
    }, 1000);
    updateIdentifyButton();
    refresh()
      .then(() => {
        setStatus("自动识别中：请直接按压手指", "live");
        scheduleAutoIdentify(300);
      })
      .catch((error) => setStatus(error.message, "err"));
  </script>
</body>
</html>`;

async function main() {
  const bridge = await startBridge();
  const server = createServer(bridge);
  const port = await listen(server, preferredPort);

  log("Attendance app ready", {
    url: `http://127.0.0.1:${port}`,
    dataFile,
  });

  async function shutdown() {
    log("Shutting down...");
    server.close();
    await bridge.shutdown();
    process.exit(0);
  }

  process.once("SIGINT", shutdown);
  process.once("SIGTERM", shutdown);
}

main().catch((error) => {
  log("Failed to start attendance app", {
    name: error.name,
    message: error.message,
    traceback: error.traceback,
  });
  process.exit(1);
});
