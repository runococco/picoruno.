// node test.js <html> <outdir> [skill] — real taps on beads and the clear button, then a bot that reads the target and flicks rod by rod (skill = time per flick + thinking time)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  // canvas maps 720 -> 390 wide; rod 4 (ones) at x 608 -> 329, earth bead 1 inactive at y ~ 871 -> ...
  const sc = 390 / 720, oy = (780 - 1280 * sc) / 2; const P = (x, y) => [x * sc, oy + y * sc];
  await pg.mouse.click(...P(608, 871)); await pg.mouse.click(...P(484, 569)); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c2-tap.png' });
  console.log('after taps', await pg.evaluate(() => __T.value()));
  await pg.mouse.click(...P(360, 1098)); await pg.waitForTimeout(200); console.log('after clear', await pg.evaluate(() => __T.value()));
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0, qref = null;
    (function bot() { const now = performance.now(); if (G.phase === 'play' && G.q && G.okT <= 0 && now > next) {
      if (qref !== G.q) { qref = G.q; next = now + 400 + 1600 * (1 - K) * (String(G.q.n).length); requestAnimationFrame(bot); return }
      const t = String(G.q.target).padStart(5, '0'); let done = false;
      // clear first if this is a fresh number and the board is not empty (like a person would)
      if (/ごはさん/.test(G.q.kind) && T.value() !== 0 && !G._cleared) { T.clearAll(); G._cleared = 1; next = now + 250; requestAnimationFrame(bot); return }
      for (let i = 0; i < 5 && !done; i++) { const d = +t[i], r = G.rods[i], h = d >= 5 ? 1 : 0, e = d % 5;
        if (r.h !== h) { T.flick(i, 'h'); done = true } else if (r.e !== e) { T.flick(i, 'e', e > r.e ? e - 1 : e); done = true } }
      if (G.okT > 0) G._cleared = 0;
      next = now + 110 + 450 * (1 - K) + Math.random() * 200 * (1 - K) }
      if (G.okT > 0) G._cleared = 0;
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(40000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, n: __T.G.solved, fast: __T.G.fast, beads: __T.G.beads, qn: __T.G.qn }))));
  console.log('errs', errs); await b.close();
})();
