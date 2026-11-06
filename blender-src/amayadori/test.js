// node test.js <html> <outdir>   — real drag first, then an in-page bot that keeps the umbrella upwind over the cat (sometimes lazy)
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  await pg.mouse.move(200, 500); await pg.mouse.down(); await pg.mouse.move(150, 520, { steps: 6 }); await pg.mouse.up();
  console.log('umb after drag', JSON.stringify(await pg.evaluate(() => __T.G.umb)));
  await pg.evaluate(() => {
    const G = __T.G; let lazy = 0;
    (function bot() {
      if (G.phase === 'play') {
        lazy = (lazy + 1) % 600;
        const tx = (G.drips.length ? G.drips[0].x : 270 - G.wind * 150) , ty = 1050 - 290;
        if (lazy < 520) __T.moveUmb((tx - G.umb.x) * .12 / 1.15, (ty - G.umb.y) * .12 / 1.15);
      }
      requestAnimationFrame(bot)
    })()
  });
  for (let n = 0; n < 5; n++) { await pg.waitForTimeout(3000); if (n === 1 || n === 3) await pg.screenshot({ path: out + `/c2-play${n}.png` }) }
  console.log(JSON.stringify(await pg.evaluate(() => ({ m: __T.meters(), wet: __T.G.wet, blocked: __T.G.blocked, greet: __T.G.greet }))));
  await pg.evaluate(() => { __T.G.dist = 99 * 60 }); await pg.waitForTimeout(1500); await pg.screenshot({ path: out + '/c3-rainbow.png' });
  await pg.evaluate(() => { __T.G.wet = .99 }); await pg.waitForTimeout(400); await pg.evaluate(() => { __T.G.umb.x = 650 }); await pg.waitForTimeout(4000);
  await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, m: __T.meters(), rb: __T.G.rainbows }))));
  console.log('errs', errs); await b.close();
})();
