// node test.js <html> <outdir> [skill] — a real tilt drag, then a bot that plans a grid path around walls/holes and steers along it (skill scales its care)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(400);
  await pg.mouse.move(200, 500); await pg.mouse.down(); await pg.mouse.move(240, 500, { steps: 6 }); await pg.waitForTimeout(500); await pg.screenshot({ path: out + '/c2-tilt.png' }); await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; const C = 15; let lv = -1, path = [], wi = 0;
    function plan() { const L = T.LEVELS[G.lv], W = Math.ceil(720 / C), H = Math.ceil(1280 / C), blk = new Uint8Array(W * H);
      for (let gy = 0; gy < H; gy++) for (let gx = 0; gx < W; gx++) { const x = gx * C + C / 2, y = gy * C + C / 2; let b = x < 60 + 21 || x > 660 - 21 || y < 210 + 21 || y > 1150 - 21;
        for (const [wx, wy, ww, wh] of L.walls) { const cx = Math.max(wx, Math.min(wx + ww, x)), cy = Math.max(wy, Math.min(wy + wh, y)); if (Math.hypot(x - cx, y - cy) < 22) b = true }
        for (const [hx, hy] of L.holes) if (Math.hypot(x - hx, y - hy) < 40) b = true; blk[gy * W + gx] = b }
      const s = [Math.floor(G.m.x / C), Math.floor(G.m.y / C)], g = [Math.floor(L.goal[0] / C), Math.floor(L.goal[1] / C)]; const prev = new Int32Array(W * H).fill(-1), q = [s[1] * W + s[0]]; prev[q[0]] = q[0]; blk[g[1] * W + g[0]] = 0;
      while (q.length) { const c = q.shift(); if (c === g[1] * W + g[0]) break; const cx = c % W, cy = (c / W) | 0; for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const nx = cx + dx, ny = cy + dy, n = ny * W + nx; if (nx < 0 || ny < 0 || nx >= W || ny >= H || blk[n] || prev[n] >= 0) continue; prev[n] = c; q.push(n) } }
      const p = []; let c = g[1] * W + g[0]; if (prev[c] < 0) return []; while (c !== prev[c]) { p.push([(c % W) * C + C / 2, ((c / W) | 0) * C + C / 2]); c = prev[c] } p.reverse(); return p.filter((_, i) => i % 3 === 0 || i === p.length - 1) }
    (function bot() { if (G.phase === 'play') {
      if (G.state !== 'roll') { T.hold(false); lv = -2 } else { if (lv !== G.lv || !path.length) { lv = G.lv; path = plan(); wi = 0 }
        const m = G.m; while (wi < path.length - 1 && Math.hypot(path[wi][0] - m.x, path[wi][1] - m.y) < 22) wi++; const w = path[wi] || G.m;
        const vmax = 140 + 220 * K, ex = w[0] - m.x, ey = w[1] - m.y, d = Math.hypot(ex, ey) || 1, tvx = ex / d * Math.min(vmax, d * 4), tvy = ey / d * Math.min(vmax, d * 4);
        const ax = (tvx - m.vx) * .012 * (K >= .6 ? 1 : .6), ay = (tvy - m.vy) * .012 * (K >= .6 ? 1 : .6); T.hold(true); T.setTilt(ax * 110, ay * 110) } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForFunction(() => __T.G.lv >= 2 && __T.G.lvT > 3, null, { timeout: 120000 }).catch(() => {}); await pg.screenshot({ path: out + '/c3-lv3.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 200000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, cl: __T.G.cleared, lives: __T.G.lives, time: (__T.G.total + __T.G.lvT).toFixed(1), lv: __T.G.lv }))));
  console.log('errs', errs); await b.close();
})();
