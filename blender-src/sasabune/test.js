// node test.js <html> <outdir> [skill] — a real tap, then a bot that picks the safest lane ahead and taps beside the boat to push it there (skill = reaction time and aim)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/c2-start.png' });
  await pg.mouse.click(120, 520); await pg.waitForTimeout(300);
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0; const gap = (.22 + (1 - K) * .5) * 1000;
    function cost(x) { let c = Math.abs(x - G.bx) * .02; for (const o of G.obs) { const sy = o.y + G.scroll, ahead = G.by - sy; if (ahead < -60 || ahead > 520) continue; const w = 1 - Math.max(0, ahead) / 600;
        if (o.k === 'rock') { const d = Math.abs(o.x - x); if (d < o.r + 50) c += 100 * w * (1 - d / (o.r + 50) * .5); if (ahead < 220 && Math.min(G.bx, x) < o.x + o.r + 30 && Math.max(G.bx, x) > o.x - o.r - 30) c += 80 }
        else if (o.k === 'log') { const lx = o.x + o.vx * Math.max(0, ahead) / G.V, d = Math.max(0, Math.abs(lx - x) - o.hl); if (d < 50) c += 100 * w }
        else if (o.k === 'uzu') { const d = Math.abs(o.x - x); if (d < o.r + 20) c += 70 * w }
        else if (o.k === 'petal' || o.k === 'icho') { if (Math.abs(o.x - x) < 40) c -= 15 * w } } return c }
    (function bot() { const now = performance.now(); if (G.phase === 'play' && now > next) { let best = G.bx, bc = 1e9; for (let x = T.RX0 + 30; x <= T.RX1 - 30; x += 10) { const c = cost(x); if (c < bc) { bc = c; best = x } }
        const err = (1 - K) * (Math.random() - .5) * 160, want = best + err, dx = want - G.bx, pred = dx - G.vx * .5;
        if (Math.abs(pred) > 30) { const s = Math.sign(pred), dist = 150 - Math.min(110, Math.abs(pred) * .5); T.tap(G.bx - s * dist, G.by + (G.by - 880) * .6 + 20); next = now + gap }
        else if (G.by < 760) { T.tap(G.bx, G.by - 120); next = now + gap } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(20000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 240000 }).catch(() => {});
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ why: __T.G.why.join(","), ph: __T.G.phase, m: Math.floor(__T.G.scroll / 50), score: __T.G.score, br: __T.G.bridges, pet: __T.G.petals, taps: __T.G.taps, hits: __T.G.hits, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
