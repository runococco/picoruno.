// node test.js <html> <outdir>   — an in-page bot that grabs a vine and steers the pull to the middle of the green band
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  await pg.screenshot({ path: out + '/c2-start.png' });
  await pg.evaluate(() => {
    const T = __T, G = T.G; let n = 0, wait = 0;
    (function bot() {
      if (G.phase === 'play') {
        if (!G.hold) { wait -= 1 / 60; if (wait <= 0) { const s = T.SLOTS.filter(q => q.v && q.v.grow > .8)[0]; if (s) { T.pdown(s.x, s.y - 40); n++ } wait = .3 } }
        else { const h = G.hold, b = T.band(h.slot.v); const want = n % 5 === 4 ? b.hi + .2 : (b.lo + b.hi) / 2; T.pmove(h.x0, h.y0 - want * T.PULLMAX) }
      }
      requestAnimationFrame(bot)
    })()
  });
  for (let n = 0; n < 6; n++) { await pg.waitForTimeout(2000); if (n === 1 || n === 4 || n === 5) await pg.screenshot({ path: out + `/c3-play${n}.png` }) }
  // real pointer drag on a vine
  console.log(JSON.stringify(await pg.evaluate(() => ({ s: __T.G.score, cnt: __T.G.cnt, snaps: __T.G.snaps }))));
  await pg.waitForTimeout(50000); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, cnt: __T.G.cnt, kg: __T.G.kg, gold: __T.G.gold, snaps: __T.G.snaps }))));
  console.log('errs', errs); await b.close();
})();
