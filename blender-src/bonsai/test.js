// node test.js <html> <outdir> [skill] — a real mouse swipe, then a bot that snips pads outside the dashed model shape
// (skill = pause between snips and how precisely it aims)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: (r.width - 720 * S) / 2, oy: (r.height - 1280 * S) / 2 } });
  await pg.screenshot({ path: out + '/c2-start.png' });
  await pg.mouse.move(box.ox + 640 * box.S, box.oy + 800 * box.S); await pg.mouse.down(); await pg.mouse.move(box.ox + 560 * box.S, box.oy + 800 * box.S, { steps: 8 }); await pg.mouse.up();
  console.log('swipe', await pg.evaluate(() => [__T.G.cut, __T.G.bad, __T.G.score]));
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0, lx = 360, ly = 500; const lag = (.12 + (1 - K) * .5) * 1000, err = (1 - K) * 40;
    (function bot() { const now = performance.now(); if (G.phase === 'play' && G.between <= 0 && now > next) {
        let best = null, bd = 1e9; for (const c of G.cells) { if (c.inT || c.g < .6 || c.re > 0) continue; const d = Math.hypot(c.x - lx, c.y - ly); if (d < bd) { bd = d; best = c } }
        if (best) { const x = best.x + (Math.random() - .5) * err, y = best.y + (Math.random() - .5) * err; T.pdown(x, y); T.pmove(x + 3, y); T.pup(); lx = x; ly = y; next = now + lag } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(30000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 90000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, cut: __T.G.cut, bad: __T.G.bad, rounds: __T.G.scores }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
