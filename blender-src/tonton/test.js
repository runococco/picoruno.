// node test.js <html> <outdir> [rate]  — a bot that taps at `rate` taps/s (eases off when wobbling if rate>0)
const { chromium } = require('playwright');
(async () => {
  const [html, out, rate] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1900);
  for (let k = 0; k < 6; k++) { await pg.mouse.click(200, 500); await pg.waitForTimeout(220) }
  await pg.screenshot({ path: out + '/c2-fight.png' });
  await pg.evaluate((R) => { const T = __T, G = T.G; let nt = 0;
    (function bot() { if (G.phase === 'play' && G.stage === 'fight' && !G.res && G.t >= nt) { const smart = R > 0, r = Math.abs(R); if (!(smart && Math.abs(G.A.th) > .4)) T.tapSide('A'); nt = G.t + 1 / r * (0.8 + Math.random() * .4) } requestAnimationFrame(bot) })() }, +(rate || 5));
  await pg.waitForFunction(() => __T.G.res, null, { timeout: 60000 }); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c3-res.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 240000 }); await pg.waitForTimeout(2200);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, w: __T.G.w, l: __T.G.l, o: __T.G.outs, f: __T.G.falls, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
