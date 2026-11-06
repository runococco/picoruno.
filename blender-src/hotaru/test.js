// node test.js <html> <outdir>   — real taps, then a bot that taps glowing fireflies (and sometimes a dark one)
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1500);
  const S = 390 / 720, OY = (780 - 1280 * S) / 2;
  for (let k = 0; k < 6; k++) { const f = await pg.evaluate(() => { const G = __T.G; const l = G.flies.find(f => __T.glowOf(f) > .5); return l ? [l.x, l.y] : null }); if (f) await pg.mouse.click(f[0] * S, f[1] * S + OY); await pg.waitForTimeout(250) }
  console.log('after real taps', await pg.evaluate(() => __T.G.count));
  await pg.screenshot({ path: out + '/c2-play.png' });
  await pg.evaluate(() => { const T = __T, G = T.G; let w = 0;
    (function bot() { if (G.phase === 'play' && --w <= 0) { w = 34; const f = G.flies.find(f => !f.flee && T.glowOf(f) > .45); if (f) T.tapAt(f.x, f.y); else if (Math.random() < .05 && G.flies[0]) T.tapAt(G.flies[0].x, G.flies[0].y) } requestAnimationFrame(bot) })() });
  await pg.waitForFunction(() => __T.G.sync > 2, null, { timeout: 30000 }); await pg.screenshot({ path: out + '/c3-sync.png' });
  await pg.waitForTimeout(12000); await pg.screenshot({ path: out + '/c4-jar.png' });
  await pg.evaluate(() => { __T.G.left = 1 }); await pg.waitForTimeout(3500);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, n: __T.G.count, c: __T.G.maxCombo, g: __T.G.gold, f: __T.G.fled }))));
  console.log('errs', errs); await b.close();
})();
