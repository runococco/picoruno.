// node test.js <html> <outdir> [skill] — a real press-and-hold, then a bot that starts pushing when the next bowl will be under the spout
// as the noodles land and lets go after the target amount (skill = timing noise)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  await pg.mouse.move(200, 600); await pg.mouse.down(); await pg.waitForTimeout(500); await pg.screenshot({ path: out + '/c2-push.png' }); await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; let tgt = null, pushed = 0, want = 0, lastLeft = 0;
    (function bot() { if (G.phase === 'play') {
        if (!tgt || tgt.done || tgt.x < T.SP[0] - T.BW[tgt.k].r * .9) { tgt = G.bowls.find(b => !b.done && b.f === 0 && b.x > T.SP[0] - T.BW[b.k].r * .5) || null; pushed = 0; want = 0 }
        if (tgt) { const B = T.BW[tgt.k], v = T.speed(), D = B.rim - T.SP[1], fall = (-240 + Math.sqrt(240 * 240 + 2 * 2300 * D)) / 2300;
          const startX = T.SP[0] + B.r * .85 + v * fall;
          if (!want && tgt.x <= startX) { want = tgt.t * (1 + (Math.random() - .5) * (1 - K) * .7); pushed = 0; lastLeft = G.left }
          if (want) { if (G.left < lastLeft) pushed += lastLeft - G.left; lastLeft = G.left; const go = pushed < want; if (go !== G.hold) T.press(go); if (!go) { tgt.f = tgt.f || 1e-9 } } } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(25000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 60000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, served: __T.G.served, perfect: __T.G.perfect, combo: __T.G.maxCombo, hearts: __T.G.hearts, t: __T.G.t.toFixed(0) }));
  if (st.ph === 'play') await pg.evaluate(() => { __T.G.hearts = 1; __T.G.bowls.forEach(b => { if (!b.done) b.f = 0 }) });
  await pg.waitForTimeout(6000); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st));
  console.log('errs', errs); await b.close();
})();
