const express = require('express');
const crypto = require('crypto');
const path = require('path');
const config = require('./config');

const app = express();

// Use express.raw for all body handling, then parse JSON dynamically if needed
app.use(express.raw({ type: '*/*', limit: '1mb' }));

const nonceStore = new Map();
let currentMode = config.MODE;

// Serve interactive browser testbed at GET /
app.get('/', (req, res) => {
  res.send(`
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FRUGAL CRYPTO VAULT — HMAC-SHA512 Security & Replay Guard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root[data-theme="dark"] {
      --bg-dark: #070A12;
      --panel-bg: #0F172A;
      --card-bg: #1E293B;
      --border-color: #334155;
      --accent-blue: #38BDF8;
      --accent-green: #10B981;
      --accent-red: #F43F5E;
      --text-main: #F8FAFC;
      --text-muted: #94A3B8;
      --terminal-bg: #020617;
    }

    :root[data-theme="bright"] {
      --bg-dark: #F1F5F9;
      --panel-bg: #FFFFFF;
      --card-bg: #F8FAFC;
      --border-color: #CBD5E1;
      --accent-blue: #0284C7;
      --accent-green: #059669;
      --accent-red: #E11D48;
      --text-main: #0F172A;
      --text-muted: #64748B;
      --terminal-bg: #FFFFFF;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg-dark);
      color: var(--text-main);
      font-family: 'Inter', sans-serif;
      padding: 30px;
      transition: background-color 0.3s ease, color 0.3s ease;
    }

    .container {
      max-width: 960px;
      margin: 0 auto;
      background: var(--panel-bg);
      border-radius: 16px;
      padding: 28px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.1);
      border: 1px solid var(--border-color);
      transition: background-color 0.3s ease, border-color 0.3s ease;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border-color);
    }

    .brand { display: flex; align-items: center; gap: 14px; }
    .brand-logo {
      width: 40px; height: 40px;
      background: linear-gradient(135deg, var(--accent-blue), #818CF8);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-weight: 900; color: #FFFFFF; font-size: 20px;
    }

    h1 { font-size: 18px; font-weight: 800; letter-spacing: -0.5px; }

    .theme-toggle-btn {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 8px 14px; border-radius: 20px;
      background: var(--card-bg); border: 1px solid var(--border-color);
      color: var(--text-main); font-size: 13px; font-weight: 600;
      cursor: pointer; font-family: 'Inter', sans-serif;
      transition: all 0.2s ease;
    }
    .theme-toggle-btn:hover { border-color: var(--accent-blue); transform: translateY(-1px); }

    .badge {
      display: inline-block; padding: 6px 14px;
      border-radius: 20px; font-weight: 700; font-size: 13px;
      font-family: 'JetBrains Mono', monospace;
    }
    .badge-secure { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-vulnerable { background: rgba(244, 63, 94, 0.15); color: var(--accent-red); border: 1px solid rgba(244, 63, 94, 0.3); }
    
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
    .card {
      background: var(--card-bg);
      padding: 20px; border-radius: 12px;
      border: 1px solid var(--border-color);
      transition: background-color 0.3s ease, border-color 0.3s ease;
    }
    .card-title { font-size: 13px; font-weight: 700; color: var(--accent-blue); text-transform: uppercase; margin-bottom: 12px; font-family: 'JetBrains Mono', monospace; }
    
    button {
      background: linear-gradient(135deg, #2563EB, #1D4ED8);
      color: white; border: none;
      padding: 10px 16px; font-size: 13px; font-weight: 600;
      border-radius: 8px; cursor: pointer;
      margin-right: 8px; margin-bottom: 8px;
      transition: all 0.2s ease;
    }
    button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }
    button.danger { background: linear-gradient(135deg, #DC2626, #B91C1C); }

    .telemetry-val { font-family: 'JetBrains Mono', monospace; color: var(--accent-green); }
    .log-box {
      height: 220px; overflow-y: auto;
      background: var(--terminal-bg); border: 1px solid var(--border-color);
      padding: 12px; border-radius: 8px;
      font-family: 'JetBrains Mono', monospace; font-size: 12px;
      transition: background-color 0.3s ease;
    }
    .log-entry { margin-bottom: 6px; }
    .log-success { color: var(--accent-green); }
    .log-error { color: var(--accent-red); font-weight: 700; }
    .log-info { color: var(--accent-blue); }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="brand">
        <div class="brand-logo">🔒</div>
        <div>
          <h1>Institutional Crypto Vault Gateway</h1>
          <div style="font-size:12px; color:var(--text-muted); font-family:'JetBrains Mono', monospace; margin-top:4px;">
            HMAC-SHA512 Signature & Nonce Replay Prevention Console
          </div>
        </div>
      </div>

      <div style="display:flex; align-items:center; gap:12px;">
        <button class="theme-toggle-btn" onclick="toggleTheme()">
          <span id="themeIcon">🌙</span>
          <span id="themeLabel">Dark Theme</span>
        </button>
        <span id="modeBadge" class="badge ${currentMode === 'SECURE' ? 'badge-secure' : 'badge-vulnerable'}">${currentMode} MODE</span>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">🔐 Gateway Controls & Mode Switcher</div>
        <button onclick="toggleMode('SECURE')">Enforce SECURE Mode</button>
        <button class="danger" onclick="toggleMode('VULNERABLE')">Enable VULNERABLE Mode</button>
      </div>

      <div class="card">
        <div class="card-title">⚡ Interactive Execution Controls</div>
        <button onclick="runFullChain()">Run Complete Replay Chain</button>
        <button onclick="step1Post()">1. POST /v1/transactions</button>
        <button onclick="step2Put()">2. PUT (Signed)</button>
        <button class="danger" onclick="step3Replay()">3. Replay (<150ms)</button>
      </div>
    </div>

    <div class="card" style="margin-bottom:20px;">
      <div class="card-title">📡 Active Session Telemetry</div>
      <div style="font-size:13px; margin-bottom:6px;"><strong>Transaction ID:</strong> <span id="txIdDisplay" class="telemetry-val">None</span></div>
      <div style="font-size:13px; margin-bottom:6px;"><strong>Challenge Token:</strong> <span id="challengeDisplay" class="telemetry-val">None</span></div>
      <div style="font-size:13px;"><strong>Last Execution Status:</strong> <span id="statusDisplay" class="telemetry-val">None</span></div>
    </div>

    <div class="card">
      <div class="card-title">📜 Execution Terminal & Security Log</div>
      <div id="logBox" class="log-box"></div>
    </div>
  </div>

  <script>
    let activeChallenge = null;
    let lastPayload = null;
    let lastHeaders = null;

    function toggleTheme() {
      const html = document.documentElement;
      const currentTheme = html.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'bright' : 'dark';
      html.setAttribute('data-theme', newTheme);
      
      document.getElementById('themeIcon').innerText = newTheme === 'dark' ? '🌙' : '☀️';
      document.getElementById('themeLabel').innerText = newTheme === 'dark' ? 'Dark Theme' : 'Bright Theme';
      log('Switched workspace theme to: ' + newTheme.toUpperCase(), 'info');
    }

    function log(msg, type = 'info') {
      const box = document.getElementById('logBox');
      const div = document.createElement('div');
      div.className = 'log-entry log-' + type;
      div.innerText = '[' + new Date().toLocaleTimeString() + '] ' + msg;
      box.appendChild(div);
      box.scrollTop = box.scrollHeight;
    }

    async function toggleMode(mode) {
      const resp = await fetch('/v1/config/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      const data = await resp.json();
      document.getElementById('modeBadge').className = 'badge ' + (data.mode === 'SECURE' ? 'badge-secure' : 'badge-vulnerable');
      document.getElementById('modeBadge').innerText = data.mode + ' MODE';
      log('Gateway Security Mode updated to: ' + data.mode, 'info');
    }

    async function step1Post() {
      log('Step 1: Dispatching POST /v1/transactions...', 'info');
      const resp = await fetch('/v1/transactions', { method: 'POST' });
      const txId = resp.headers.get('X-Transaction-Id');
      const data = await resp.json();
      activeChallenge = { txId, ...data };
      document.getElementById('txIdDisplay').innerText = txId;
      document.getElementById('challengeDisplay').innerText = data.challengeToken.substring(0, 16) + '...';
      log('Received 201 Created. TxID: ' + txId, 'success');
      return activeChallenge;
    }

    async function step2Put() {
      if (!activeChallenge) await step1Post();
      log('Step 2: Computing HMAC-SHA512 signature & sending PUT...', 'info');
      const timestampMicros = Date.now() * 1000;
      lastPayload = JSON.stringify({ action: "TRANSFER", amount: 500, currency: "USD", recipient: "acc_884920" });
      
      const sigResp = await fetch('/v1/util/sign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payload: lastPayload,
          timestampMicros,
          challengeToken: activeChallenge.challengeToken,
          salt: activeChallenge.salt
        })
      });
      const { mac } = await sigResp.json();

      lastHeaders = {
        'Content-Type': 'application/json',
        'X-Frugal-Mac': mac,
        'X-Frugal-Timestamp': String(timestampMicros),
        'X-Frugal-Challenge': activeChallenge.challengeToken
      };

      const resp = await fetch('/v1/transactions/' + activeChallenge.txId, {
        method: 'PUT',
        headers: lastHeaders,
        body: lastPayload
      });

      const resData = await resp.json();
      document.getElementById('statusDisplay').innerText = resp.status + ' ' + (resData.status || resData.error);
      log('PUT Completed. Status: ' + resp.status + ' ' + JSON.stringify(resData), resp.status === 200 ? 'success' : 'error');
    }

    async function step3Replay() {
      if (!lastHeaders) {
        log('Error: Run Step 2 first to generate signed headers.', 'error');
        return;
      }
      log('Step 3: Resending byte-identical payload (Replay Attack)...', 'info');
      const start = performance.now();
      const resp = await fetch('/v1/transactions/' + activeChallenge.txId, {
        method: 'PUT',
        headers: lastHeaders,
        body: lastPayload
      });
      const gapMs = (performance.now() - start).toFixed(2);
      const resData = await resp.json();
      
      if (resp.status === 409) {
        log('REPLAY REJECTED (409 Conflict) in ' + gapMs + 'ms! Nonce Guard Triggered: ' + resData.error, 'success');
      } else if (resp.status === 200) {
        log('WARNING: REPLAY ACCEPTED (200 OK) in ' + gapMs + 'ms! Security Vulnerability Alert Generated!', 'error');
      }
    }

    async function runFullChain() {
      await step1Post();
      await step2Put();
      await step3Replay();
    }
  </script>
</body>
</html>
  `);
});

// Mode toggle endpoint with buffer parsing
app.post('/v1/config/mode', (req, res) => {
  let bodyData = req.body;
  if (Buffer.isBuffer(req.body)) {
    try { bodyData = JSON.parse(req.body.toString('utf8')); } catch(e){}
  }
  if (bodyData && bodyData.mode) {
    currentMode = bodyData.mode;
  }
  res.json({ mode: currentMode });
});

// Signature helper endpoint for web UI
app.post('/v1/util/sign', (req, res) => {
  let bodyData = req.body;
  if (Buffer.isBuffer(req.body)) {
    try { bodyData = JSON.parse(req.body.toString('utf8')); } catch(e){}
  }
  const { payload, timestampMicros, challengeToken, salt } = bodyData;
  const signingKey = crypto.createHmac('sha256', config.SHARED_SECRET).update(challengeToken).digest();
  const payloadToSign = payload + ':' + timestampMicros + ':' + salt;
  const mac = crypto.createHmac('sha512', signingKey).update(payloadToSign).digest('hex');
  res.json({ mac });
});

// POST /v1/transactions -> Initiate transaction challenge
app.post('/v1/transactions', (req, res) => {
  const txId = crypto.randomUUID();
  const challengeToken = crypto.randomBytes(32).toString('hex');
  const serverTimestampMicros = Date.now() * 1000;

  res.setHeader('X-Transaction-Id', txId);
  res.status(201).json({
    challengeToken,
    serverTimestampMicros,
    salt: config.SECRET_SALT
  });
});

// PUT /v1/transactions/:id -> Complete signed transaction
app.put('/v1/transactions/:id', (req, res) => {
  const txId = req.params.id;
  const mac = req.headers['x-frugal-mac'];
  const timestampStr = req.headers['x-frugal-timestamp'];
  const challenge = req.headers['x-frugal-challenge'];

  if (!mac || !timestampStr || !challenge) {
    return res.status(401).json({ error: 'MISSING_AUTHENTICATION_HEADERS' });
  }

  const timestampMicros = parseInt(timestampStr, 10);
  const nowMicros = Date.now() * 1000;

  if (Math.abs(nowMicros - timestampMicros) > config.MAX_CLOCK_SKEW_MICROS) {
    return res.status(422).json({ error: 'STALE_TIMESTAMP_SKEW_EXCEEDED' });
  }

  const rawBodyStr = Buffer.isBuffer(req.body) ? req.body.toString('utf8') : (typeof req.body === 'string' ? req.body : JSON.stringify(req.body));
  
  const signingKey = crypto.createHmac('sha256', config.SHARED_SECRET).update(challenge).digest();
  const payloadToSign = rawBodyStr + ':' + timestampStr + ':' + config.SECRET_SALT;
  const expectedMac = crypto.createHmac('sha512', signingKey).update(payloadToSign).digest('hex');

  const macBuffer = Buffer.from(mac, 'hex');
  const expectedBuffer = Buffer.from(expectedMac, 'hex');

  if (macBuffer.length !== expectedBuffer.length || !crypto.timingSafeEqual(macBuffer, expectedBuffer)) {
    return res.status(401).json({ error: 'INVALID_HMAC_SIGNATURE' });
  }

  const nonceKey = `${mac}:${timestampStr}`;
  if (nonceStore.has(nonceKey)) {
    if (currentMode === 'SECURE') {
      return res.status(409).json({
        error: 'REPLAY_DETECTED',
        message: 'Duplicate request detected within nonce TTL window.'
      });
    } else {
      console.warn(`[VULNERABLE GATEWAY WARNING] Replay attack permitted for transaction ${txId}`);
    }
  }

  nonceStore.set(nonceKey, timestampMicros);

  res.status(200).json({
    status: 'SUCCESS',
    txId,
    mode: currentMode,
    processedAt: Date.now() * 1000
  });
});

app.listen(config.PORT, () => {
  console.log(`[Q2 Gateway] Running in ${currentMode} mode at http://localhost:${config.PORT}`);
});
