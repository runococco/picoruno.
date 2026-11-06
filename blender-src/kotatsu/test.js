// node test.js <html> <outdir>   — a real pull-and-release + blow taps, then a bot plays the rest at 3x speed
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1200);
  console.log('phase', await pg.evaluate(() => __T.G.phase));
  await pg.mouse.move(195, 560); await pg.mouse.down(); await pg.mouse.move(185, 650, { steps: 8 });
  await pg.screenshot({ path: out + '/c2-aim.png' });
  await pg.mouse.up(); await pg.waitForTimeout(200);
  for (let i = 0; i < 6; i++) { await pg.mouse.click(300, 400); await pg.waitForTimeout(120) }
  await pg.screenshot({ path: out + '/c3-roll.png' });
  await pg.waitForTimeout(2500);
  console.log('after shot', JSON.stringify(await pg.evaluate(() => __T.G.stones.map(s => [s.k, Math.round(s.x), Math.round(s.y), Math.round(__T.dT(s))]))));
  await pg.waitForFunction(() => __T.G.phase === 'cat' && __T.G.catT > .5, null, { timeout: 8000 }); await pg.screenshot({ path: out + '/c4-cat.png' });
  await pg.evaluate(() => {
    const T = __T, G = T.G; __T.setTS(3);
    (function bot() {
      if (G.phase === 'aim' && !G.botBusy) { G.botBusy = 1; setTimeout(() => { G.botBusy = 0; if (G.phase !== 'aim') return;
        const tx = T.TX + (Math.random() - .5) * 60, ty = T.TY + (Math.random() - .5) * 60, D = Math.hypot(tx - T.LX, ty - T.LY);
        const a = Math.atan2(tx - T.LX, -(ty - T.LY)) + (Math.random() - .5) * .05, v = Math.sqrt(2 * T.MU * D) * (1 + (Math.random() - .5) * .1); T.fire(Math.sin(a) * v, -Math.cos(a) * v) }, 150) }
      requestAnimationFrame(bot)
    })()
  });
  let shotScore = false;
  for (let n = 0; n < 60; n++) { await pg.waitForTimeout(500); const ph = await pg.evaluate(() => __T.G.phase); if (ph === 'score' && !shotScore) { shotScore = true; await pg.screenshot({ path: out + '/c5-score.png' }) } if (ph === 'end') break }
  await pg.waitForTimeout(2600);
  await pg.screenshot({ path: out + '/c6-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, sc: __T.G.score, log: __T.G.endLog, pin: __T.G.pin }))));
  console.log('errs', errs); await b.close();
})();
