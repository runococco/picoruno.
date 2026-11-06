// node test.js <html> <outdir> [skill] — real pour/swipe, then a bot (skill 1 = pours to the green band, pops bubbles, rolls in the green zone)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(400);
  await pg.mouse.move(200, 400); await pg.mouse.down(); await pg.waitForTimeout(1200); await pg.screenshot({ path: out + '/c2-pour.png' }); await pg.waitForTimeout(800); await pg.mouse.up();
  await pg.waitForTimeout(1500); await pg.screenshot({ path: out + '/c3-cook.png' });
  await pg.waitForFunction(() => __T.G.d > .6, null, { timeout: 10000 }).catch(() => {});
  await pg.mouse.move(200, 300); await pg.mouse.down(); await pg.mouse.move(200, 420, { steps: 5 }); await pg.mouse.up();
  await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c4-roll.png' });
  console.log('real', await pg.evaluate(() => [__T.G.layers.length, __T.G.score]));
  await pg.evaluate((K) => { const T = __T, G = T.G; let tgtF = 0, tgtD = 0;
    (function bot() { if (G.phase === 'play') {
      if (G.state === 'ready') { tgtF = K >= 1 ? .92 : .6 + Math.random() * .55; T.pourStart() }
      if (G.state === 'pour' && G.f >= tgtF) { T.pourEnd(); tgtD = K >= 1 ? .66 : .3 + Math.random() * .7 }
      if (G.state === 'cook') { for (const bb of G.bubbles.slice()) if (Math.random() < K * .08) T.popAt(bb.x, bb.y); if (G.d >= tgtD) T.roll() } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForFunction(() => __T.G.state === 'cut', null, { timeout: 90000 }).catch(() => {}); await pg.waitForTimeout(500); await pg.screenshot({ path: out + '/c5-cut.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 150000 }).catch(() => {});
  await pg.waitForTimeout(2400); await pg.screenshot({ path: out + '/c6-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, j: __T.G.justN, pop: __T.G.popN, pour: __T.G.pourN, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
