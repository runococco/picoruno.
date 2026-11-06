// node test.js <html> <outdir> [tol]  — a bot that taps when the moving part is within tol px of a free spot
const { chromium } = require('playwright');
(async () => {
  const [html, out, tol] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c2-show.png' });
  await pg.waitForFunction(() => __T.G.stage === 'place', null, { timeout: 8000 }); await pg.waitForTimeout(700);
  await pg.mouse.click(200, 400); await pg.waitForTimeout(900);
  await pg.screenshot({ path: out + '/c3-place.png' });
  await pg.evaluate((TOL) => { const T = __T, G = T.G;
    (function bot() { if (G.phase === 'play') { if (G.stage === 'place' && G.cur && G.cur.t > .4) { const taken = G.placed.map(p => p.slot); let d = 1e9; for (const s of G.cur.slots) { if (taken.includes(s)) continue; const f = T.fpos(s); d = Math.min(d, Math.hypot(f[0] - G.cur.pos[0], f[1] - G.cur.pos[1])) } const f0 = G.cur.slots.filter(s => !taken.includes(s)).map(s => T.fpos(s)); const dd = G.cur.ax === 'x' ? Math.min(...f0.map(f => Math.abs(f[0] - G.cur.pos[0]))) : Math.min(...f0.map(f => Math.abs(f[1] - G.cur.pos[1]))); if (dd < TOL && Math.random() < .5) T.tapAny() }
        else if (G.stage === 'reveal' && G.st > 2.2) T.tapAny() } requestAnimationFrame(bot) })() }, +(tol || 25));
  await pg.waitForFunction(() => __T.G.stage === 'reveal' && __T.G.st > 1.6, null, { timeout: 60000 }); await pg.screenshot({ path: out + '/c4-reveal.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }); await pg.waitForTimeout(2500);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, f: __T.G.faces.map(f => f.score), p: __T.G.perfects, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
