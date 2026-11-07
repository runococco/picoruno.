// node test.js <html> <outdir> [skill] — real mouse drags, then a bot that predicts where the shuttle comes down and swings up under it (skill = aim noise and lag)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(300);
  await pg.mouse.move(195, 640); await pg.mouse.down(); for (let i = 0; i < 8; i++) { await pg.mouse.move(150 + i * 10, 640); await pg.waitForTimeout(40) } await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; let err = 0, errT = 0;
    function landX(yLine) { const H = G.hane; let x = H.x, y = H.y, vx = H.vx, vy = H.vy; for (let i = 0; i < 400; i++) { const dt = 1 / 120, sp = Math.hypot(vx, vy); vx += (-T.DRAG * sp * vx + G.wind) * dt; vy += (T.GRAV - T.DRAG * sp * vy) * dt; x += vx * dt; y += vy * dt; if (x < 20) { x = 20; vx = Math.abs(vx) * .6 } if (x > 700) { x = 700; vx = -Math.abs(vx) * .6 } if (vy > 0 && y >= yLine) return [x, i / 120] } return [x, 9] }
    (function bot() { if (G.phase === 'play' && G.hane.live && G.wait <= 0) { const now = performance.now(); if (now > errT) { err = (1 - K) * (Math.random() - .5) * 140; errT = now + 600 }
        const [lx, tt] = landX(920), dir = G.targets.length ? Math.sign(G.targets[0].x - lx) * 10 : 0; const swing = tt < .12; T.aim(lx + err - dir, (swing ? 840 : 990) + T.LIFT) }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(25000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 80000 }).catch(() => {});
  if (await pg.evaluate(() => __T.G.phase === 'play')) await pg.evaluate(() => { __T.G.inks = 2; __T.G.hane.x = 30; __T.G.hane.y = 1100; __T.G.hane.vy = 400 });
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, hits: __T.G.hits, best: __T.G.best, popped: __T.G.popped, inks: __T.G.inks, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
