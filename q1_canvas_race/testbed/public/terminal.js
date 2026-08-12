(function() {
  const canvas = document.getElementById('terminal');
  const ctx = canvas.getContext('2d');
  const params = new URLSearchParams(window.location.search);
  const seed = params.get('seed') || '42';

  let latestData = null;
  let hasError = false;
  let errorMessage = "";
  let frameCount = 0;
  let renderTs = performance.now();
  const priceHistory = [];
  window.__SHOW_DEBUG_RETICLE__ = true;
  window.__CANVAS_THEME__ = 'dark';

  window.__TERMINAL_STATE__ = {
    frameCount: 0,
    lastSeq: 0,
    renderTs: performance.now(),
    cellStates: {}
  };

  // Connect WebSocket
  const wsUrl = `ws://${window.location.host}/stream?seed=${seed}`;
  const ws = new WebSocket(wsUrl);
  window.__TERMINAL_WS__ = ws;

  ws.onmessage = (event) => {
    try {
      const boundaryEnabled = new URLSearchParams(window.location.search).get('boundary') !== 'off';
      const data = JSON.parse(event.data);

      if (data.phase === 'live') {
        const isCorrupt = !isFinite(data.price) || data.price > 100000 || data.price < 0 || (data.price.toString().length > 10);
        
        if (isCorrupt && boundaryEnabled) {
          hasError = true;
          errorMessage = `CRITICAL DATA ERROR: Out-of-bounds price payload received (${data.price})`;
          return;
        }
      }

      latestData = data;
      window.__TERMINAL_STATE__.lastSeq = data.seq || 0;
      
      if (data.price && isFinite(data.price)) {
        priceHistory.push(data.price);
        if (priceHistory.length > 50) priceHistory.shift();
      }

      if (data.cells) {
        data.cells.forEach(c => {
          window.__TERMINAL_STATE__.cellStates[c.id] = c.state;
        });
      }
    } catch (err) {
      const boundaryEnabled = new URLSearchParams(window.location.search).get('boundary') !== 'off';
      if (boundaryEnabled) {
        hasError = true;
        errorMessage = `PARSE ERROR: ${err.message}`;
      }
    }
  };

  // Helper: Draw Rounded Rect
  function drawRoundedRect(x, y, width, height, radius, fillStyle, strokeStyle = null) {
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, radius);
    if (fillStyle) {
      ctx.fillStyle = fillStyle;
      ctx.fill();
    }
    if (strokeStyle) {
      ctx.strokeStyle = strokeStyle;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }

  // Draw High-Tech Reticle Overlay for Pixel Calibration Inspection
  function drawTargetReticle(cx, cy, cellId, isActive, isDark) {
    ctx.save();
    ctx.strokeStyle = isActive ? (isDark ? '#10B981' : '#059669') : (isDark ? '#38BDF8' : '#0284C7');
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);

    ctx.beginPath(); ctx.moveTo(cx - 15, cy); ctx.lineTo(cx + 15, cy); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx, cy - 15); ctx.lineTo(cx, cy + 15); ctx.stroke();

    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.arc(cx, cy, 8, 0, Math.PI * 2);
    ctx.strokeStyle = isActive ? (isDark ? '#34D399' : '#059669') : (isDark ? '#38BDF8' : '#0284C7');
    ctx.stroke();

    ctx.fillStyle = isActive ? (isDark ? '#34D399' : '#059669') : (isDark ? '#38BDF8' : '#0284C7');
    ctx.font = '9px "JetBrains Mono", monospace';
    ctx.fillText(`[${cx},${cy}]`, cx - 18, cy - 12);
    ctx.restore();
  }

  // Render loop
  function render() {
    frameCount++;
    renderTs = performance.now();
    window.__TERMINAL_STATE__.frameCount = frameCount;
    window.__TERMINAL_STATE__.renderTs = renderTs;

    const isDark = (window.__CANVAS_THEME__ || 'dark') === 'dark';

    // Theme Colors
    const bgColor = isDark ? '#020617' : '#FFFFFF';
    const gridColor = isDark ? '#0F172A' : '#F1F5F9';
    const headerBg = isDark ? '#0F172A' : '#F8FAFC';
    const headerBorder = isDark ? '#1E293B' : '#E2E8F0';
    const titleColor = isDark ? '#F8FAFC' : '#0F172A';

    // 1. Clear background
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid lines
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 40) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 40) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
    }

    // 2. Header Bar
    ctx.fillStyle = headerBg;
    ctx.fillRect(0, 0, canvas.width, 64);
    ctx.strokeStyle = headerBorder;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, 64); ctx.lineTo(canvas.width, 64); ctx.stroke();

    ctx.font = 'bold 18px "JetBrains Mono", monospace';
    ctx.fillStyle = titleColor;
    ctx.fillText('FRGL / USD QUANTUM ORDERBOOK', 24, 40);

    if (hasError) {
      // Red Error Banner & ERR Glyph
      ctx.fillStyle = '#DC2626';
      ctx.fillRect(0, 64, canvas.width, 36);
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 13px "JetBrains Mono", monospace';
      ctx.fillText(errorMessage, 24, 87);

      drawRoundedRect(840, 16, 96, 32, 6, '#EF4444', '#F87171');
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 14px "JetBrains Mono", monospace';
      ctx.fillText('⚠️ ERR', 860, 38);

    } else if (latestData && latestData.phase === 'live') {
      // Live Ticker Stats
      const isUp = latestData.delta >= 0;
      ctx.font = 'bold 16px "JetBrains Mono", monospace';
      ctx.fillStyle = isUp ? (isDark ? '#10B981' : '#059669') : (isDark ? '#F43F5E' : '#E11D48');
      const tickerText = `$${latestData.price.toFixed(2)} (${isUp ? '+' : ''}${latestData.delta.toFixed(2)})`;
      ctx.fillText(tickerText, 640, 40);

      // Price Curve Overlay
      if (priceHistory.length > 2) {
        ctx.beginPath();
        const minP = Math.min(...priceHistory);
        const maxP = Math.max(...priceHistory) || minP + 1;
        
        for (let i = 0; i < priceHistory.length; i++) {
          const px = 420 + (i / 50) * 200;
          const py = 50 - ((priceHistory[i] - minP) / (maxP - minP)) * 30;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.strokeStyle = isUp ? (isDark ? '#10B981' : '#059669') : (isDark ? '#F43F5E' : '#E11D48');
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // 3. Render 6x4 Grid
      const startX = 60;
      const startY = 130;
      const cellW = 120;
      const cellH = 100;
      const gapX = 20;
      const gapY = 20;

      if (latestData.cells) {
        latestData.cells.forEach(cell => {
          const col = cell.x;
          const row = cell.y;
          const x = startX + col * (cellW + gapX);
          const y = startY + row * (cellH + gapY);
          const cx = x + Math.floor(cellW / 2);
          const cy = y + Math.floor(cellH / 2);

          if (cell.state === 'loading') {
            const dither = (frameCount + cell.id) % 5 - 2;
            const grayVal = Math.min(255, Math.max(0, 128 + dither));
            const fill = `rgb(${grayVal}, ${grayVal}, ${grayVal})`;
            drawRoundedRect(x, y, cellW, cellH, 8, fill, '#475569');

            ctx.fillStyle = '#1E293B';
            ctx.font = 'bold 11px "JetBrains Mono", monospace';
            ctx.fillText(`ORDER #${cell.id}`, x + 12, y + 25);
            ctx.font = '12px "JetBrains Mono", monospace';
            ctx.fillText(`SYNCING...`, x + 12, y + 60);

          } else {
            const isGreen = cell.id % 2 === 0;
            const fill = isDark 
              ? (isGreen ? '#064E3B' : '#881337') 
              : (isGreen ? '#D1FAE5' : '#FFE4E6');
            const border = isDark 
              ? (isGreen ? '#10B981' : '#F43F5E') 
              : (isGreen ? '#059669' : '#E11D48');
            const txtColor = isDark
              ? (isGreen ? '#34D399' : '#FB7185')
              : (isGreen ? '#065F46' : '#9F1239');

            drawRoundedRect(x, y, cellW, cellH, 8, fill, border);

            ctx.fillStyle = isDark ? '#F8FAFC' : '#0F172A';
            ctx.font = 'bold 12px "JetBrains Mono", monospace';
            ctx.fillText(`ORDER #${cell.id}`, x + 12, y + 25);

            ctx.font = 'bold 16px "JetBrains Mono", monospace';
            ctx.fillStyle = txtColor;
            ctx.fillText(`$${cell.v.toFixed(2)}`, x + 12, y + 58);

            drawRoundedRect(x + 12, y + 70, 56, 18, 4, border);
            ctx.fillStyle = '#FFFFFF';
            ctx.font = '9px "JetBrains Mono", monospace';
            ctx.fillText(isGreen ? 'ASK DEPTH' : 'BID DEPTH', x + 14, y + 83);
          }

          if (window.__SHOW_DEBUG_RETICLE__) {
            drawTargetReticle(cx, cy, cell.id, cell.state === 'active', isDark);
          }
        });
      }
    } else {
      ctx.fillStyle = isDark ? '#94A3B8' : '#64748B';
      ctx.font = '16px "JetBrains Mono", monospace';
      ctx.fillText('CONNECTING TO HIGH-FREQUENCY ORDERBOOK STREAM...', 240, 320);
    }

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);
})();
