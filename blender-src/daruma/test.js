// node test.js <html> <outdir> [skill] — real taps, then a bot (skill 1 = hits inside the green band, from the side that pulls the stack back)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(700);
  await pg.screenshot({ path: out + '/c2-ready.png' });
  await pg.mouse.click(80, 500); await pg.waitForTimeout(60); await pg.screenshot({ path: out + '/c3-hit.png' });
  await pg.waitForTimeout(500); await pg.mouse.click(310, 500); await pg.waitForTimeout(700); await pg.screenshot({ path: out + '/c4-after.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let tgt = null;
    (function bot() { if (G.phase === 'play' && G.state === 'ready') {
      const mid = (G.band[0] + G.band[1]) / 2, w = G.band[1] - G.band[0];
      if (tgt === null) tgt = mid + (Math.random() * 2 - 1) * (w * .3 + (1 - K) * .25);
      if (Math.abs(G.p - tgt) < .02 && G.stT > .25) { T.hit(G.off > 0 ? -1 : 1); tgt = null } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForFunction(() => __T.G.tw >= 3 && __T.G.blocks.length === 4, null, { timeout: 90000 }).catch(() => {}); await pg.screenshot({ path: out + '/c5-tower4.png' });
  await pg.waitForFunction(() => __T.G.state === 'fall' || __T.G.state === 'done', null, { timeout: 60000 }).catch(() => {}); await pg.waitForTimeout(250); await pg.screenshot({ path: out + '/c6-event.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 200000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c7-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, tw: __T.G.towerN, cl: __T.G.cleanN, pf: __T.G.perfN, lives: __T.G.lives, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
