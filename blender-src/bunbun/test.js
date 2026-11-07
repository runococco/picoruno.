// node test.js <html> <outdir> [skill] — real presses, then a bot that pulls when the disc stalls and lets go when the string is straight (skill = reaction lag)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1900);
  await pg.mouse.move(195, 500); await pg.mouse.down(); await pg.waitForTimeout(300); await pg.mouse.up(); await pg.waitForTimeout(200);
  await pg.evaluate((K) => { const T = __T, G = T.G, lag = (.03 + (1 - K) * .25) * 1000; let pend = null, pendT = 0;
    (function bot() { if (G.phase === 'play' && G.state === 'spin') { const want = G.pull ? (Math.abs(G.tau) > .4 && G.om * G.tau < 0) : (G.om * G.tau <= 0 && Math.abs(G.tau) > 1);
      const now = performance.now(); if (want !== pend) { pend = want; pendT = now } if (now - pendT >= lag && G.pull !== pend) T.setPull(pend) }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(12000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, total: __T.G.total, rr: __T.G.roundRot, peak: (__T.G.peak / 6.28).toFixed(1), boon: __T.G.boonN }))));
  console.log('errs', errs); await b.close();
})();
