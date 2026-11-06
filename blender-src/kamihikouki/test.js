const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + html); await pg.waitForTimeout(1000);
  await pg.screenshot({ path: out + '/k1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  await pg.screenshot({ path: out + '/k2-ready.png' });
  // no input: how far does a pure glide go?
  await pg.mouse.down(); await pg.waitForTimeout(80); await pg.mouse.up();
  let t0 = Date.now(); let shot = 0;
  while (Date.now() - t0 < 20000) {
    const s = await pg.evaluate(() => ({ ph: __T.G.phase, x: __T.P.x, y: __T.P.y, v: __T.P.v }));
    if (s.ph !== 'fly') break;
    await pg.waitForTimeout(250);
    if (!shot && s.x > 15) { shot = 1; await pg.screenshot({ path: out + '/k3-fly.png' }) }
  }
  console.log('no-input glide', await pg.evaluate(() => ({ ph: __T.G.phase, x: __T.P.x })));
  await pg.waitForTimeout(2000);
  await pg.screenshot({ path: out + '/k4-result.png' });
  // simple autopilot: hold when low or near obstacle, release when slow
  await pg.click('#againBtn'); await pg.waitForTimeout(400);
  await pg.evaluate(() => {
    window.__ap = setInterval(() => { const P = __T.P, G = __T.G; if (G.phase === 'ready') { __T.go() }
      const ahead = G.obs.filter(o => !o.deco && o.x > P.x && o.x < P.x + 4); const need = ahead.length ? 3.6 : 2.2;
      P.hold = (P.y < need && P.v > 3.2) || (P.v > 9 && P.y < 9) }, 30) });
  await pg.waitForTimeout(300); t0 = Date.now(); let s;
  while (Date.now() - t0 < 45000) { s = await pg.evaluate(() => ({ ph: __T.G.phase, x: Math.round(__T.P.x), y: +__T.P.y.toFixed(1), v: +__T.P.v.toFixed(1), stars: __T.G.starN })); if (s.ph !== 'fly') break; await pg.waitForTimeout(500);
    if (s.x > 120 && !shot2) { var shot2 = 1; await pg.screenshot({ path: out + '/k5-far.png' }) } }
  console.log('autopilot', JSON.stringify(s));
  await pg.waitForTimeout(2200);
  await pg.screenshot({ path: out + '/k6-result.png' });
  console.log('errs', errs);
  await b.close();
})();
