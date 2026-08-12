const express = require('express');
const http = require('http');
const path = require('path');
const WebSocket = require('ws');

const app = express();
const port = 8081;

// Serve static frontend files
app.use(express.static(path.join(__dirname, 'public')));

const server = http.createServer(app);
const wss = new WebSocket.Server({ server, path: '/stream' });

// Simple pseudo-random number generator seeded for deterministic frame output
function PRNG(seed) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return function() {
    return (s = (s * 16807) % 2147483647) / 2147483647;
  };
}

wss.on('connection', (ws, req) => {
  const urlParams = new URLSearchParams(req.url.replace(/^.*\?/, ''));
  const seedVal = parseInt(urlParams.get('seed') || '42', 10);
  const rng = PRNG(seedVal);

  let seq = 0;
  // Schedule cell state transitions (grid 6x4 = 24 cells)
  // Each cell flips loading -> active at a deterministic sequence number between 15 and 45
  const cellFlipSeqs = Array.from({ length: 24 }, (_, i) => Math.floor(15 + rng() * 30));

  let currentPrice = 148.50;

  // Initial loading phase (12 frames)
  const loadingInterval = setInterval(() => {
    if (ws.readyState !== WebSocket.OPEN) {
      clearInterval(loadingInterval);
      return;
    }
    seq++;
    const epochMicros = Date.now() * 1000;
    ws.send(JSON.stringify({
      phase: "loading",
      seq,
      t: epochMicros
    }));

    if (seq >= 12) {
      clearInterval(loadingInterval);
      startLiveStream();
    }
  }, 40);

  function startLiveStream() {
    const liveInterval = setInterval(() => {
      if (ws.readyState !== WebSocket.OPEN) {
        clearInterval(liveInterval);
        return;
      }
      seq++;
      const epochMicros = Date.now() * 1000;
      const priceDelta = (rng() - 0.48) * 0.75;
      currentPrice = Math.max(10.0, currentPrice + priceDelta);

      const cells = [];
      for (let y = 0; y < 4; y++) {
        for (let x = 0; x < 6; x++) {
          const id = y * 6 + x;
          const isActive = seq >= cellFlipSeqs[id];
          cells.push({
            id,
            x,
            y,
            state: isActive ? "active" : "loading",
            v: Math.round((currentPrice + (id % 5) * 0.12) * 100) / 100
          });
        }
      }

      ws.send(JSON.stringify({
        phase: "live",
        seq,
        t: epochMicros,
        symbol: "FRGL",
        price: Math.round(currentPrice * 100) / 100,
        delta: Math.round(priceDelta * 100) / 100,
        cells
      }));
    }, 40);
  }
});

server.listen(port, () => {
  console.log(`[Q1 Testbed] Server running at http://localhost:${port}`);
  console.log(`[Q1 Testbed] WebSocket stream at ws://localhost:${port}/stream`);
});
