// node test.js <html> <outdir> [skill] — a real tap and a real swipe, then a bot that cools the hottest stone in front of the chicks (skill = reaction time and aim)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  await pg.mouse.click(195, 500); await pg.waitForTimeout(300);
  await pg.mouse.move(150, 600); await pg.mouse.down(); for (let i = 1; i <= 6; i++) { await pg.mouse.move(150, 600 - i * 25); await pg.waitForTimeout(30) } await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0; const gap = (.35 + (1 - K) * .8) * 1000;
    (function bot() { const now = performance.now(); if (G.phase === 'play' && now > next && G.ladles >= 1) { let best = null, bv = 1.1 - (1 - K) * .3;
        for (const k of G.chicks) { if (k.state !== 'walk' || k.r < 1) continue; const r0 = Math.min(k.r, T.NR) - 1; for (const c of [k.tcl, k.c]) { let v = 0, n = 0; for (let r = r0; r >= Math.max(0, r0 - 2); r--) { const t = G.tiles[r][c]; if (t.w < .25) v += t.h; n++ } if (v > bv) { bv = v; best = [r0, Math.max(0, r0 - 2), c] } } }
        if (best) { const a = T.tc(best[0], best[2]), z = T.tc(best[1], best[2]), e = (1 - K) * 50; T.splash(a[0] + (Math.random() - .5) * e, a[1] - 10, z[0] + (Math.random() - .5) * e, z[1]); next = now + gap } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(30000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, home: __T.G.home, burnt: __T.G.burnt, hearts: __T.G.hearts, splashes: __T.G.splashes, left: __T.G.left.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
