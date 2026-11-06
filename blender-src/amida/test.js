// node test.js <html> <outdir> [skill] — real taps, then a bot (skill 1 = always draws a rung that leads to the big fish during the countdown)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  await pg.mouse.click(195 * .5 + 100, 420); await pg.waitForTimeout(500);
  await pg.screenshot({ path: out + '/c2-look.png' });
  await pg.waitForTimeout(3000); await pg.screenshot({ path: out + '/c3-walk.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let lv = -1, at = 0;
    (function bot() { if (G.phase === 'play' && G.state === 'look') {
      if (lv !== G.lv) { lv = G.lv; at = .3 + Math.random() * 1.2 }
      if (G.stT > at && at >= 0) { at = -1; const big = G.plates.findIndex(p => p.k === 'big'); const c = [];
        for (let a = 0; a < G.N - 1; a++) for (let y = T.TOP + 40; y < T.BOT - 40; y += 6) if (T.okAt(G.rungs, a, y) && T.trace(G.start, G.rungs.concat([{ a, y }])) === big) c.push([a, y]);
        if (c.length && Math.random() < K) { const [a, y] = c[Math.floor(Math.random() * c.length)]; T.tapAt((G.X[a] + G.X[a + 1]) / 2, y) }
        else { const a = Math.floor(Math.random() * (G.N - 1)); T.tapAt((G.X[a] + G.X[a + 1]) / 2, T.TOP + 60 + Math.random() * 560) } } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForFunction(() => __T.G.lv >= 4 && __T.G.state === 'walk', null, { timeout: 60000 }).catch(() => {}); await pg.waitForTimeout(700); await pg.screenshot({ path: out + '/c4-lv5.png' });
  await pg.waitForFunction(() => __T.G.state === 'eat', null, { timeout: 20000 }).catch(() => {}); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c5-eat.png' });
  await pg.waitForFunction(() => __T.G.lv >= 8 && __T.G.state === 'walk', null, { timeout: 80000 }).catch(() => {}); await pg.waitForTimeout(600); await pg.screenshot({ path: out + '/c6-lv9.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 150000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c7-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, lv: __T.G.lv, big: __T.G.bigN, sm: __T.G.smallN, d: __T.G.dangoN, e: __T.G.emptyN, lives: __T.G.lives, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
