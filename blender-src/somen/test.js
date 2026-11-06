// node test.js <html> <outdir>   — a few real taps, then an in-page bot that taps when food is in the ring (skips leaves, sometimes late)
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(2500);
  await pg.mouse.click(100, 500); await pg.waitForTimeout(300); await pg.mouse.click(300, 500); await pg.waitForTimeout(200);
  console.log('after real taps', JSON.stringify(await pg.evaluate(() => ({ s: __T.G.score, eat: __T.G.eat, lane: __T.G.hashi.lane }))));
  await pg.evaluate(() => {
    const T = __T, G = T.G;
    (function bot() {
      if (G.phase === 'play') for (const l of [0, 1]) { const it = G.items.find(i => i.lane === l && !i.got && Math.abs(i.y - T.CY) < 14 + Math.random() * 20); if (it && it.k !== 'leaf' && Math.random() < .5) T.tap(l) }
      requestAnimationFrame(bot)
    })()
  });
  await pg.waitForTimeout(6000); await pg.screenshot({ path: out + '/c2-play.png' });
  await pg.waitForTimeout(20000); await pg.screenshot({ path: out + '/c3-play.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ s: __T.G.score, eat: __T.G.eat, cat: __T.G.catAte, combo: __T.G.maxCombo, left: __T.G.left }))));
  await pg.evaluate(() => { __T.G.left = 1.5 }); await pg.waitForTimeout(4200);
  await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score }))));
  console.log('errs', errs); await b.close();
})();
