// node test.js <html> <outdir> [stopAt]  — a bot that holds during the chant and lets go at mora index stopAt
const { chromium } = require('playwright');
(async () => {
  const [html, out, stopAt] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1600);
  await pg.mouse.move(200, 600); await pg.mouse.down(); await pg.waitForTimeout(1300);
  await pg.screenshot({ path: out + '/c2-walk.png' }); await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G;
    (function bot() { if (G.phase === 'play') { const want = G.stage === 'run' && G.oni === 'back' && G.mi < K && G.mi >= -1; if (want !== G.hold) T.press(want) } requestAnimationFrame(bot) })() }, +(stopAt || 7));
  await pg.waitForFunction(() => __T.G.oni === 'watch', null, { timeout: 30000 }); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c3-watch.png' });
  await pg.waitForFunction(() => __T.G.stage === 'over', null, { timeout: 120000 }); await pg.waitForTimeout(600); await pg.screenshot({ path: out + '/c4-touch.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 240000 }); await pg.waitForTimeout(2200);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, f: __T.G.firsts, c: __T.G.caught, p: __T.G.places, best: __T.G.best.toFixed(1), t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
