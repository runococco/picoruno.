// node test.js <html> <outdir> [fitK]  — a real hold/release, then a bot that blows bubbles sized fitK * the hoop opening and times them
const { chromium } = require('playwright');
(async () => {
  const [html, out, fk] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  await pg.mouse.move(200, 500); await pg.mouse.down(); await pg.waitForTimeout(700);
  await pg.screenshot({ path: out + '/c2-blow.png' });
  await pg.mouse.up(); await pg.waitForTimeout(900);
  console.log('real', await pg.evaluate(() => [__T.G.bubbles.length, __T.G.bubbles[0] && Math.round(__T.G.bubbles[0].r)]));
  await pg.evaluate((K) => { const T = __T, G = T.G; let plan = null;
    function holdFor(r) { let x = 12, t = 0; while (x < r) { x += 58 * (1 - .25 * Math.min(1, x / 120)) / 60; t += 1 / 60 } return t }
    (function bot() { if (G.phase === 'play') {
      if (!plan && !G.blow && G.cool <= 0) for (const h of G.hoops) { const r = Math.min(110, h.R * .93 * K), th = holdFor(r), p = T.blowPos(r), vy = 232 - r * 1.15, hy = T.hoopY(h), tr = (p[1] - hy) / vy;
          const fx = h.x + h.vx * (th + tr); if (Math.abs(fx - p[0]) < 12 && hy < p[1] - 60) { plan = { r }; T.press(); break } }
      if (plan && G.blow && G.blow.r >= plan.r) { T.release(); plan = null } if (plan && !G.blow && G.cool > 0) { plan = null; T.release() } }
      requestAnimationFrame(bot) })() }, +(fk || .75));
  await pg.waitForTimeout(20000); await pg.screenshot({ path: out + '/c3-play.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 90000 }).catch(() => {});
  await pg.waitForTimeout(2600);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, p: __T.G.passes, f: __T.G.fits, g: __T.G.golds, pops: __T.G.pops, mc: __T.G.maxCombo, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
