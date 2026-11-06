const { chromium } = require('playwright');
(async () => {
  const [html, out, mode] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/h1-title.png' });
  await pg.click('#startBtn');
  if (mode === 'ap') await pg.evaluate(() => { setInterval(() => { const B = __T.B; if (B.state !== 'burn' && B.state !== 'light') return; const bx = B.ax + Math.sin(B.th) * 250; __T.moveAcc.x += (bx - B.ax) * .12 + Math.sin(B.th) * B.om * 6 }, 16) });
  const shots = { 2: 'h2-botan', 16: 'h3-matsuba', 30: 'h4-yanagi', 40: 'h5-chiri' }; const done = {};
  const t0 = Date.now();
  while (Date.now() - t0 < 170000) {
    const s = await pg.evaluate(() => ({ ph: __T.G.phase, st: __T.B.state, burn: __T.B.burn, stick: __T.G.stick, n: __T.G.results.length }));
    if (s.ph === 'result') break;
    if (s.stick === 0 && s.st === 'burn') for (const k in shots) if (!done[k] && s.burn > +k) { done[k] = 1; await pg.screenshot({ path: out + `/${shots[k]}.png` }) }
    if (s.st === 'fall' && !done.fall) { done.fall = 1; await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/h6-fall.png' }) }
    await pg.waitForTimeout(200);
  }
  console.log(JSON.stringify(await pg.evaluate(() => ({ score: __T.G.score, res: __T.G.results.map(r => [r.full, r.secs.toFixed(1), r.calm.toFixed(2)]) }))));
  await pg.waitForTimeout(1600); await pg.screenshot({ path: out + '/h7-result.png' });
  console.log('errs', errs); await b.close();
})();
