// node test.js <html> <outdir>   — a bot that taps when the gauge is in the yellow zone (sometimes a bit early or late)
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c2-start.png' });
  await pg.mouse.click(200, 500); await pg.waitForTimeout(600);   // a real tap at a random moment
  await pg.evaluate(() => {
    const { G } = __T; let n = 0;
    (function bot() {
      if (!window.__stopBot && G.phase === 'play' && G.st === 'ready') {
        const z = __T.zones(G.stack[0]), p = (1 - Math.cos(G.ph)) / 2, rising = Math.sin(G.ph) > 0;
        const aim = n % 9 === 8 ? z.weak - .1 : n % 6 === 5 ? z.good - .04 : (z.good + z.perf) / 2;
        if (rising && p >= aim) { n++; __T.tap() }
      }
      requestAnimationFrame(bot)
    })()
  });
  for (let n = 0; n < 6; n++) { await pg.waitForTimeout(2500); if (n === 1 || n === 4) await pg.screenshot({ path: out + `/c3-play${n}.png` }) }
  console.log(JSON.stringify(await pg.evaluate(() => ({ s: __T.G.score, lv: __T.G.lv, lives: __T.G.lives, perf: __T.G.perf, st: __T.G.st }))));
  await pg.evaluate(() => { window.__stopBot = 1; __T.G.lives = 1 });
  for (let n = 0; n < 40; n++) { await pg.waitForTimeout(1000); if (await pg.evaluate(() => __T.G.phase) === 'end') break; await pg.evaluate(() => { const G = __T.G; if (G.st === 'ready') { G.ph = Math.PI * .3; __T.tap() } }) }
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, lv: __T.G.lv, lives: __T.G.lives }))));
  console.log('errs', errs); await b.close();
})();
