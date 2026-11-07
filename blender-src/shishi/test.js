// node test.js <html> <outdir> [skill] — real taps on the lanes, then a bot that keeps tubes pre-filled and tops one off when a heron is close (skill = reaction lag)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  await pg.mouse.click(70, 500); await pg.waitForTimeout(700); await pg.mouse.click(300, 500); await pg.waitForTimeout(500);
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0; const lag = (.1 + (1 - K) * .7) * 1000, pre = .8 + K * .1;
    (function bot() { const now = performance.now(); if (G.phase === 'play' && now > next) { let want = null;
        // a heron that will be close soon: top off its tube so the clack lands while it is deep in range
        let urg = 1e9; for (const h of G.herons) { if (h.st !== 'come') continue; const tb = G.tubes[h.l]; if (tb.st !== 'rest') continue; const need = (1 - tb.f) * T.FILL + .85 + (h.l !== G.lane ? .3 : 0);
          const tGood = (T.POND - 40 - h.y) / h.vy; if (tGood < need + .3 && tGood < urg) { urg = tGood; want = h.l } }
        if (want === null) { let lo = 1e9; G.tubes.forEach((tb, l) => { if (tb.st === 'rest' && tb.f < pre && tb.f < lo) { lo = tb.f; want = l } }) }
        if (want === null) { const tb = G.tubes[G.lane]; if (tb.f >= pre) { for (let l = 0; l < 3; l++) if (G.tubes[l].st !== 'rest' || l !== G.lane) { want = l; break } } }
        if (want !== null && want !== G.lane) { T.pick(want); next = now + lag } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(30000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 85000 }).catch(() => {});
  if (await pg.evaluate(() => __T.G.phase === 'play')) await pg.evaluate(() => { __T.G.koiLeft = 1; __T.G.herons.push({ l: 0, x: 120, y: __T.POND - 1, vy: 50, face: 1, st: 'come', t: 0, vx: 0 }) });
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, scared: __T.G.scared, close: __T.G.close, koi: __T.G.koiLeft, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
