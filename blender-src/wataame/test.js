// node test.js <html> <outdir> [skill] — a real circular drag, then a bot that circles the pan at a chosen speed and hands over near the dashed size (skill = speed control + timing)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1200);
  const sc = 390 / 720, oy = (780 - 1280 * sc) / 2; const P = (x, y) => [x * sc, oy + y * sc];
  await pg.mouse.move(...P(360 + 180, 700)); await pg.mouse.down();
  for (let i = 0; i <= 60; i++) { const a = i / 60 * Math.PI * 4; await pg.mouse.move(...P(360 + Math.cos(a) * 180, 700 + Math.sin(a) * 180)); await pg.waitForTimeout(16) }
  await pg.screenshot({ path: out + '/c2-spin.png' }); await pg.mouse.up();
  console.log('after drag', await pg.evaluate(() => __T.G.size.toFixed(3)));
  await pg.evaluate((K) => { const T = __T, G = T.G; let a = 0, om = rnd(), o = null, stop = 0;
    function rnd() { return 8.5 + (Math.random() - .5) * 10 * (1 - K) }
    (function bot() { if (G.phase === 'play' && G.state === 'spin') {
      if (o !== G.order) { o = G.order; stop = o.sz * (1 + (Math.random() - .5) * .35 * (1 - K)) - .02 }
      if (Math.random() < .03) om = rnd();
      a += om / 60; T.moveAt(T.CX + Math.cos(a) * 180, T.CY + Math.sin(a) * 180, performance.now());
      if (G.size >= stop) T.hand() } else if (G.phase === 'play') T.up();
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(30000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, sold: __T.G.sold, perf: __T.G.perfect, tears: __T.G.tears }))));
  console.log('errs', errs); await b.close();
})();
