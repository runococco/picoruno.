// node test.js <html> <outdir> [skill] — a real mouse press-and-hold, then a bot that holds on the biggest hole and lets go
// when the patch matches it (skill = reaction lag and how accurately it judges the size)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.stack.slice(0, 300))); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(2500);
  await pg.screenshot({ path: out + '/c2-start.png' });
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: r.left + (r.width - 720 * S) / 2, oy: r.top + (r.height - 1280 * S) / 2 } });
  const h0 = await pg.evaluate(() => { const h = __T.G.holes[0]; return h && { x: h.x, y: h.y } });
  if (h0) { await pg.mouse.move(box.ox + h0.x * box.S, box.oy + h0.y * box.S); await pg.mouse.down(); await pg.waitForTimeout(500); await pg.mouse.up(); }
  console.log('mouse hold', await pg.evaluate(() => [__T.G.patched, __T.G.score]));
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0, target = 0; const lag = (.15 + (1 - K) * .6) * 1000;
    (function bot() { const now = performance.now(); if (G.phase === 'play') {
        if (G.hold) { if (G.hold.r >= G.hold.h.r + target) { T.up(); next = now + lag } }
        else if (now > next && G.holes.length) { const h = G.holes.slice().sort((a, b) => b.r - a.r)[0]; target = 6 + (Math.random() - .5) * (1 - K) * 50; T.down(h.x, h.y) } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(25000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, t: Math.round(__T.G.t), cold: Math.round(__T.G.cold), patched: __T.G.patched, perfect: __T.G.perfect, combo: __T.G.maxCombo }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
