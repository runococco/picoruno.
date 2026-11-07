// node test.js <html> <outdir> [skill] — a real mouse tap, then a bot that taps where the equal cuts should be,
// with an aiming error and a pause between taps that grow as skill drops
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.stack.slice(0, 300))); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(700);
  await pg.screenshot({ path: out + '/c2-start.png' });
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: r.left + (r.width - 720 * S) / 2, oy: r.top + (r.height - 1280 * S) / 2 } });
  await pg.mouse.click(box.ox + 362 * box.S, box.oy + 624 * box.S);
  console.log('mouse tap', await pg.evaluate(() => [__T.G.cuts.length, !!__T.G.judged, __T.G.accs]));
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0; const lag = (.25 + (1 - K) * .6) * 1000, err = (1 - K) * 30;
    (function bot() { const now = performance.now(); if (G.phase === 'play' && !G.judged && G.between <= 0 && now > next) {
        const e = SCENE.veg[G.veg], a = 40 + e[0] + G.drift, len = e[1] - e[0]; const k = G.cuts.length + 1; const x = a + len * k / G.n + (Math.random() - .5) * err; T.down(x, 624); next = now + lag }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(12000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase === 'end', null, { timeout: 120000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, accs: __T.G.accs, perfect: __T.G.perfect }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
