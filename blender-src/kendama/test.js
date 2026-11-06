// node test.js <html> <outdir>   — an in-page autopilot that steers the cup the mission asks for under the falling ball and taps to toss
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  await pg.evaluate(() => {
    const { G, K, B, restPt } = __T; let wait = 0;
    (function bot() {
      if (G.phase === 'play') {
        if (B.on) { wait += 1 / 60; if (wait > .35) { wait = 0; __T.toss(true) } }
        else if (B.missed) { wait += 1 / 60; if (wait > .5) { wait = 0; __T.toss(true) } }
        else if (B.vy > -200) {
          let want = G.mis[G.misStep] || 'big'; if (want === 'spike' && Math.abs(Math.atan2(Math.sin(B.spin), Math.cos(B.spin))) > .5) want = 'big';
          const p = restPt(want);
          // predict where the ball crosses the cup height
          const dy = p.y - B.y, t = (-B.vy + Math.sqrt(Math.max(0, B.vy * B.vy + 2 * 2300 * Math.max(0, dy)))) / 2300;
          const px = B.x + B.vx * t; K.tx += (px - p.x) * .5; K.tx = Math.max(90, Math.min(630, K.tx));
        }
      }
      requestAnimationFrame(bot)
    })()
  });
  for (let n = 0; n < 8; n++) { await pg.waitForTimeout(1500); if (n === 1 || n === 4) await pg.screenshot({ path: out + `/c2-play${n}.png` }) }
  // real input check: drag + tap
  const T = await pg.evaluate(() => ({ s: document.getElementById('cv').getBoundingClientRect() }));
  await pg.mouse.move(200, 600); await pg.mouse.down(); await pg.mouse.move(150, 560, { steps: 5 }); await pg.mouse.up();
  await pg.mouse.click(200, 650);
  console.log(JSON.stringify(await pg.evaluate(() => ({ s: __T.G.score, c: __T.G.cnt, mc: __T.G.maxCombo, md: __T.G.misDone }))));
  await pg.waitForTimeout(50000); await pg.screenshot({ path: out + '/c3-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, c: __T.G.cnt, mc: __T.G.maxCombo, md: __T.G.misDone }))));
  console.log('errs', errs); await b.close();
})();
