const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const port = 8000;
app.use(express.json());

// Serve Master Dashboard UI at GET /
app.get('/', (req, res) => {
  res.send(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FRUGAL TESTING AI-NATIVE INTERN EXECUTION CONTROL CENTER</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #070A12;
      --panel-bg: #0F172A;
      --card-bg: #1E293B;
      --border-color: #334155;
      --accent-blue: #38BDF8;
      --accent-green: #10B981;
      --accent-purple: #818CF8;
      --accent-red: #F43F5E;
      --text-main: #F8FAFC;
      --text-muted: #94A3B8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-dark);
      color: var(--text-main);
      font-family: 'Inter', sans-serif;
      padding: 30px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(15, 23, 42, 0.9);
      backdrop-filter: blur(12px);
      padding: 20px 30px;
      border-radius: 16px;
      border: 1px solid var(--border-color);
      margin-bottom: 24px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .title-group { display: flex; align-items: center; gap: 16px; }
    .logo {
      width: 44px; height: 44px;
      background: linear-gradient(135deg, #38BDF8, #818CF8);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-weight: 900; color: #070A12; font-size: 22px;
    }
    .title { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
    .subtitle { font-size: 13px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }
    
    .grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin-bottom: 24px;
    }
    .card {
      background: var(--panel-bg);
      border-radius: 16px;
      border: 1px solid var(--border-color);
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
      transition: all 0.3s ease;
    }
    .card:hover { border-color: var(--accent-blue); transform: translateY(-2px); }
    .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
    .card-tag { font-size: 11px; font-family: 'JetBrains Mono', monospace; padding: 4px 10px; border-radius: 20px; background: rgba(56, 189, 248, 0.1); color: var(--accent-blue); border: 1px solid rgba(56, 189, 248, 0.3); font-weight: 600; }
    .card-title { font-size: 16px; font-weight: 700; color: var(--text-main); margin-bottom: 6px; }
    .card-desc { font-size: 13px; color: var(--text-muted); line-height: 1.5; margin-bottom: 16px; }
    
    .btn {
      display: inline-flex; align-items: center; justify-content: center;
      padding: 10px 18px; border-radius: 8px; border: none;
      font-family: 'Inter', sans-serif; font-weight: 600; font-size: 13px;
      cursor: pointer; text-decoration: none; transition: all 0.2s ease;
    }
    .btn-primary { background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3); }
    .btn-primary:hover { background: linear-gradient(135deg, #1D4ED8, #1E40AF); }

    .test-runner-card {
      background: var(--panel-bg);
      border-radius: 16px;
      border: 1px solid var(--border-color);
      padding: 24px;
      margin-bottom: 24px;
    }
    .terminal-box {
      background: #020617;
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 16px;
      height: 240px;
      overflow-y: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: var(--accent-blue);
    }
  </style>
</head>
<body>

  <div class="header">
    <div class="title-group">
      <div class="logo">F</div>
      <div>
        <div class="title">Frugal Testing AI-Native Execution Control Center</div>
        <div class="subtitle">Candidate: &lt;YOUR_NAME&gt; · Master Unified Suite & Evaluation Platform</div>
      </div>
    </div>
    <div>
      <span style="font-family:'JetBrains Mono', monospace; font-size:12px; color:var(--accent-green); background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); padding:6px 14px; border-radius:20px; font-weight:600;">
        🟢 ALL SYSTEMS OPERATIONAL
      </span>
    </div>
  </div>

  <div class="grid">
    <!-- Q1 Card -->
    <div class="card">
      <div>
        <div class="card-header">
          <span class="card-tag">Q1 MODULE</span>
          <span style="color:var(--accent-green); font-size:12px; font-family:'JetBrains Mono', monospace;">PORT 8081</span>
        </div>
        <div class="card-title">Canvas Terminal & WS Race Interception</div>
        <div class="card-desc">rAF pixel-color state classifier, dynamic calibration scan, Fibonacci jitter, circuit breaker, & sub-100ms chained actions.</div>
      </div>
      <a href="http://localhost:8081" target="_blank" class="btn btn-primary">Launch Q1 Terminal ↗</a>
    </div>

    <!-- Q2 Card -->
    <div class="card">
      <div>
        <div class="card-header">
          <span class="card-tag">Q2 MODULE</span>
          <span style="color:var(--accent-green); font-size:12px; font-family:'JetBrains Mono', monospace;">PORT 8082</span>
        </div>
        <div class="card-title">HMAC Replay Guard & Gateway Console</div>
        <div class="card-desc">HMAC-SHA512 header signer, challenge tokens, constant-time verification, SECURE / VULNERABLE modes, & CWE-294 security alerts.</div>
      </div>
      <a href="http://localhost:8082" target="_blank" class="btn btn-primary">Launch Q2 Security Gateway ↗</a>
    </div>

    <!-- Q3 Card -->
    <div class="card">
      <div>
        <div class="card-header">
          <span class="card-tag">Q3 MODULE</span>
          <span style="color:var(--accent-green); font-size:12px; font-family:'JetBrains Mono', monospace;">PORT 8083</span>
        </div>
        <div class="card-title">Closed Shadow DOM & AX Tree Inspector</div>
        <div class="card-desc">Element.prototype.attachShadow monkey-patch, deep boundary traverser, CDP AX-tree role-path locator, & CoT System Prompt.</div>
      </div>
      <a href="http://localhost:8083" target="_blank" class="btn btn-primary">Launch Q3 Shadow Inspector ↗</a>
    </div>
  </div>

  <div class="test-runner-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
      <h3 style="color:var(--accent-blue); font-size:16px;">⚡ Automated Pytest Suite Execution Control</h3>
      <button class="btn btn-primary" onclick="runPytest()">Run All 11 Pytest Verification Tests</button>
    </div>
    <div id="terminalBox" class="terminal-box">
      Click "Run All 11 Pytest Verification Tests" above to execute the automated suite live...
    </div>
  </div>

  <script>
    async function runPytest() {
      const box = document.getElementById('terminalBox');
      box.innerText = '[EXEC] Launching PYTHONPATH=. pytest -v across Q1, Q2, and Q3...\n';
      
      const resp = await fetch('/api/run-pytest', { method: 'POST' });
      const data = await resp.json();
      box.innerText += data.output;
      box.scrollTop = box.scrollHeight;
    }
  </script>

</body>
</html>
  `);
});

// API endpoint to trigger live pytest run
app.post('/api/run-pytest', (req, res) => {
  exec('PYTHONPATH=. ./venv/bin/pytest -v', { cwd: __dirname }, (error, stdout, stderr) => {
    res.json({
      success: !error,
      output: stdout || stderr || error.message
    });
  });
});

app.listen(port, () => {
  console.log(`[Master Control Center] Running at http://localhost:${port}`);
});
