const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/g1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  const S = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const s = Math.max(r.width / 720, r.height / 1280); return { s, ox: (r.width - 720 * s) / 2, oy: (r.height - 1280 * s) / 2 } });
  const cl = (x, y) => [S.ox + x * S.s, S.oy + y * S.s];
  let shot = 0;
  for (let k = 0; k < 40; k++) {
    const st = await pg.evaluate(() => ({ ph: __T.G.phase, t: __T.G.t, fish: __T.G.fish.filter(f => f.alpha > .9).map(f => ({ x: f.x, y: f.y, a: f.a, sp: f.sp, kind: f.kind })), score: __T.G.score }));
    if (st.ph !== 'play') break;
    const f = st.fish[k % st.fish.length];
    // dip a little behind the fish, follow it, lift
    let [x, y] = cl(f.x - Math.cos(f.a) * 10, f.y - Math.sin(f.a) * 10);
    await pg.mouse.move(x, y); await pg.mouse.down();
    for (let i = 0; i < 6; i++) { const g = await pg.evaluate(fx => { const f = __T.G.fish.find(q => Math.abs(q.x - fx.x) < 60 && Math.abs(q.y - fx.y) < 60); return f ? { x: f.x, y: f.y } : null }, f); if (g) { [x, y] = cl(g.x, g.y); await pg.mouse.move(x, y, { steps: 2 }) } await pg.waitForTimeout(60); }
    if (shot === 0 && k === 2) { shot = 1; await pg.screenshot({ path: out + '/g2-under.png' }) }
    await pg.mouse.up(); await pg.waitForTimeout(150);
    if (k === 3) await pg.screenshot({ path: out + '/g3-fly.png' });
    await pg.waitForTimeout(250);
  }
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, t: __T.G.t.toFixed(1), score: __T.G.score, caught: __T.G.caught, pois: __T.G.poisLeft, life: __T.G.poi.life.toFixed(0) }))));
  await pg.screenshot({ path: out + '/g4-mid.png' });
  await pg.waitForFunction(() => __T.G.phase === 'result', null, { timeout: 70000 }); await pg.waitForTimeout(1800);
  await pg.screenshot({ path: out + '/g5-result.png' });
  console.log('errs', errs);
  await b.close();
})();
