// node test.js <html> <outdir> [skill] — a real press-and-drag, then a bot that keeps the syrup on the thirstiest cluster of grains (skill = retarget speed and aim)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1800);
  await pg.mouse.move(150, 520); await pg.mouse.down(); for (let i = 0; i < 10; i++) { await pg.mouse.move(150 + i * 8, 520 + i * 3); await pg.waitForTimeout(60) } await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0, tgt = null; const gap = (.12 + (1 - K) * .5) * 1000;
    function pick() { let best = null, bv = -1e9; for (const c of G.gr) { let v = 0, bad = false; for (const g of G.gr) { if (Math.hypot(g.x - c.x, g.y - c.y) < T.SR + T.radius(g) * .5) { if (g.wet > T.STICKY * (.4 + .5 * K)) bad = true; v += g.ok ? -.3 : 1 - g.s + g.burn * 3 * K } } if (bad) continue; if (v > bv) { bv = v; best = c } } return best }
    (function bot() { const now = performance.now(); if (G.phase === 'play' && G.state === 'cook') { if (now > next) { tgt = pick(); next = now + gap }
        if (tgt && G.gr.includes(tgt)) { const e = (1 - K) * 30; const x = tgt.x + tgt.vx * .08 + (Math.random() - .5) * e, y = tgt.y + tgt.vy * .08 + (Math.random() - .5) * e - T.DY; if (G.pour) T.move(x, y); else T.press(x, y) } else if (G.pour) T.release() }
      else if (G.pour) T.release(); requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(16000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 240000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, done: __T.G.done, clumps: __T.G.clumps, burnt: __T.G.burnt, perfect: __T.G.perfect, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
