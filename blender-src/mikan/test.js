const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/m1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(900);
  await pg.screenshot({ path: out + '/m2-start.png' });
  const S = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const s = Math.max(r.width / 720, r.height / 1280); return { s, ox: (r.width - 720 * s) / 2, oy: (r.height - 1280 * s) / 2 } });
  const cl = (x, y) => [S.ox + (x + 360) * S.s, S.oy + (y + 610) * S.s];
  // speeds per fruit (px per step); fruit 3 deliberately too fast, fruit 5 wanders off
  const plan = [6, 7, 30, 7, 7, 7];
  for (let f = 0; f < 6; f++) {
    await pg.waitForFunction(() => __T.F.state === 'peel', null, { timeout: 8000 });
    const P = await pg.evaluate(() => __T.F.sp.pts); const N = P.length - 1;
    let [x, y] = cl(P[0][0], P[0][1]); await pg.mouse.move(x, y); await pg.mouse.down();
    let k = 0, acc = 0;
    while (k < N) {
      // walk along the path by plan[f] px of arc per step (one step ≈ 16ms)
      let d = 0; while (k < N && d < plan[f]) { d += Math.hypot(P[k + 1][0] - P[k][0], P[k + 1][1] - P[k][1]); k++ }
      let [px, py] = [P[k][0], P[k][1]];
      if (f === 4 && k > N * .4) { px += 70; }   // drift off the line
      [x, y] = cl(px, py); await pg.mouse.move(x, y); await pg.waitForTimeout(14);
      const st = await pg.evaluate(() => __T.F.state); if (st !== 'peel') break;
      if (f === 1 && k > N * .5 && !acc) { acc = 1; await pg.screenshot({ path: out + '/m3-peel.png' }) }
    }
    await pg.mouse.up();
    const r = await pg.evaluate(() => { const r = __T.G.results[__T.G.results.length - 1]; return r ? { full: r.full, pct: r.pct.toFixed(2), cm: r.cm.toFixed(0), bonus: r.bonus } : null });
    console.log('fruit', f, JSON.stringify(r));
    if (f === 0) { await pg.waitForTimeout(500); await pg.screenshot({ path: out + '/m4-done.png' }) }
  }
  await pg.waitForFunction(() => __T.G.phase === 'result', null, { timeout: 8000 }); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/m5-result.png' });
  console.log('score', await pg.evaluate(() => __T.G.score), 'errs', errs);
  await b.close();
})();
