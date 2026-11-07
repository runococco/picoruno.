// node test.js <html> <outdir> [skill] — a real press-and-hold, then a bot that searches aim + wind with the game's own walk rule (skill adds aim/wind error)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1200);
  await pg.mouse.move(230, 300); await pg.mouse.down(); await pg.waitForTimeout(900); await pg.screenshot({ path: out + '/c2-wind.png' }); await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; let plan = null;
    function gauss() { return (Math.random() + Math.random() + Math.random() - 1.5) / .5 }
    (function bot() { if (G.phase === 'play') {
      if (G.state === 'aim' && !plan) { const k = G.cur.k, [tx, ty] = T.cfg().t; let best = null;
        // aim a little off-centre now and then so later toys knock earlier ones in rather than stopping short behind them
        const off = G.toys.length > 1 ? (Math.random() - .5) * 40 : 0;
        for (let a = -.6; a <= .6; a += .03) for (let w = .3; w <= 1.25; w += .02) { const [x, y, cl] = T.predict(a, w, k); const d = Math.hypot(x - tx - off, y - ty) + (cl < 6 ? 500 : 0); if (!best || d < best.d) best = { a, w, d } }
        const a = best.a + gauss() * .05 * (1 - K), w = best.w + gauss() * .09 * (1 - K);
        plan = { a, w, t0: performance.now() }; T.press(T.SX + Math.sin(a) * 300, T.SY - Math.cos(a) * 300) }
      if (plan && G.state === 'wind' && G.W >= plan.w) { T.release(); plan = null }
      if (plan && G.state !== 'wind') plan = null }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForFunction(() => __T.G.round >= 1 && __T.G.toys.length >= 3, null, { timeout: 120000 }).catch(() => {}); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.state === 'tally' && __T.G.round === 2, null, { timeout: 200000 }).catch(() => {}); await pg.waitForTimeout(1500); await pg.screenshot({ path: out + '/c3b-tally.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 200000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, c: __T.G.centerN, on: __T.G.onN, fall: __T.G.fallN, t: __T.G.t.toFixed(1) }))));
  console.log('errs', errs); await b.close();
})();
