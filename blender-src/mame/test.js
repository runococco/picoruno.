// node test.js <html> <outdir> [skill] — a real drag, then a bot (skill 1 = picks valuable beans, carries at 60% of the slip speed, waits out the cat paw)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  const p = await pg.evaluate(() => { const b = __T.G.beans[0], r = document.getElementById('cv').getBoundingClientRect(), S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)), OX = (r.width - 720 * S) / 2, OY = (r.height - 1280 * S) / 2; return { x: b.x * S + OX, y: b.y * S + OY, bx: __T.BX * S + OX, by: __T.BY * S + OY } });
  await pg.mouse.move(p.x, p.y); await pg.mouse.down(); await pg.mouse.move((p.x + p.bx) / 2, (p.y + p.by) / 2, { steps: 20 }); await pg.screenshot({ path: out + '/c2-carry.png' });
  await pg.mouse.move(p.bx, p.by, { steps: 20 }); await pg.mouse.up(); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c3-in.png' });
  console.log('real', await pg.evaluate(() => [__T.G.inN, __T.G.slipN]));
  await pg.evaluate((K) => { const T = __T, G = T.G; let lt = performance.now();
    const val = { gold: 4, black: 3, azuki: 2, soy: 1 };
    (function bot(n) { const dt = Math.min(.05, (n - lt) / 1000) || .016; lt = n; if (G.phase === 'play') {
      if (!G.held) { const bs = G.beans.slice().sort((a, b) => (val[b.k] - val[a.k]) * (K >= .8 ? 1 : 0) + (Math.random() - .5) * .1); const t = bs[0]; if (t) T.grab(t.x, t.y) }
      else { const h = G.held, lim = T.KIND[h.k].lim, v = lim * (.6 + (1 - K) * .8), dx = T.BX - h.x, dy = T.BY - h.y, d = Math.hypot(dx, dy);
        const pawNear = K >= .8 && G.paw && G.paw.t < 1.7 && Math.abs(h.y - G.paw.y) < 140;
        if (d < 30) T.release(); else if (!pawNear) { const s = Math.min(d, v * dt); T.move(h.x + dx / d * s, h.y + dy / d * s, dt) } } }
      requestAnimationFrame(bot) })(performance.now()) }, K);
  await pg.waitForFunction(() => __T.G.paw && __T.G.paw.t > 1, null, { timeout: 40000 }).catch(() => {}); await pg.screenshot({ path: out + '/c4-paw.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 90000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, in: __T.G.inN, bl: __T.G.blackN, slip: __T.G.slipN, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
