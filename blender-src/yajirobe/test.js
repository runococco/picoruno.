// node test.js <html> <outdir> [skill] — a real drag-and-drop, then a bot that drops each weight on the side that cancels the current tilt (skill scales aim and greed)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1200);
  await pg.mouse.move(195, 200); await pg.mouse.down(); await pg.mouse.move(120, 200, { steps: 6 }); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c2-drag.png' }); await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; let plan = null, cur = null;
    (function bot() { if (G.phase === 'play' && G.cur && !G.cur.drop) {
      if (cur !== G.cur) { cur = G.cur; const m = T.KIND[cur.k].m; let tq = 0; for (const it of G.items) tq += it.m * (it.lx / T.REACH) * 3;
        // aim to cancel the torque and lean against the angle, greedier skilled bots go wide
        const want = -tq - G.th * 6 - G.om * 2; let lx = want / (m * 3) * T.REACH; const side = Math.sign(lx) || (Math.random() < .5 ? -1 : 1);
        lx = Math.max(-T.REACH * .97, Math.min(T.REACH * .97, lx)); if (Math.abs(lx) < T.REACH * .3 * K) lx = side * T.REACH * .3 * K;
        lx += (Math.random() - .5) * T.REACH * .5 * (1.1 - K); plan = { lx, wait: 300 + Math.random() * 700 * (1.2 - K), t0: performance.now() } }
      if (performance.now() - plan.t0 > plan.wait) { const x = 360 + plan.lx * Math.cos(G.th); T.holdAt(x); if (performance.now() - plan.t0 > plan.wait + 120) T.release() } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForFunction(() => __T.G.items.length >= 8, null, { timeout: 120000 }).catch(() => {}); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 300000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, n: __T.G.placedN, m: __T.G.mass.toFixed(1), miss: __T.G.missN, t: __T.G.t.toFixed(1) }))));
  console.log('errs', errs); await b.close();
})();
