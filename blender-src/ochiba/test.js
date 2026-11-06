// node test.js <html> <outdir> [bot=1]
const { chromium } = require('playwright');
(async () => {
  const [html, out, bot = '1'] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/o1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  await pg.screenshot({ path: out + '/o2-start.png' });
  const t0 = Date.now(); let shot = 0;
  const T = await pg.evaluate(() => __T.toFrame());
  const scr = (x, y) => [T.OX + x * T.S, T.OY + y * T.S];
  while (Date.now() - t0 < 56000) {
    const st = await pg.evaluate(() => ({ ph: __T.G.phase, t: __T.G.t, pct: __T.G.pct }));
    if (st.ph !== 'play') break;
    if (bot === '1') {
      // pick the leaf farthest from the fire among a random few, sweep it from behind toward the fire
      const l = await pg.evaluate(() => { const F = __T.FIRE; const L = __T.G.leaves.filter(l => Math.hypot(l.x - F.x, l.y - F.y) > F.r);
        if (!L.length) return null; let best = L[0]; for (let i = 0; i < 6; i++) { const c = L[Math.floor(Math.random() * L.length)]; if (Math.hypot(c.x - F.x, c.y - F.y) < Math.hypot(best.x - F.x, best.y - F.y)) best = c }
        return { x: best.x, y: best.y, fx: F.x, fy: F.y } });
      if (l) {
        const dx = l.fx - l.x, dy = l.fy - l.y, d = Math.hypot(dx, dy), ux = dx / d, uy = dy / d;
        const sx = l.x - ux * 50, sy = l.y - uy * 50, ex = l.x + ux * Math.min(d - 40, 220), ey = l.y + uy * Math.min(d - 40, 220);
        let [a, c] = scr(sx, sy); await pg.mouse.move(a, c); await pg.mouse.down();
        for (let i = 1; i <= 10; i++) { [a, c] = scr(sx + (ex - sx) * i / 10, sy + (ey - sy) * i / 10); await pg.mouse.move(a, c); await pg.waitForTimeout(16) }
        await pg.mouse.up();
      }
    } else await pg.waitForTimeout(300);
    if (Math.floor(st.t / 5) !== Math.floor((st.t - .3) / 5)) console.log('t', st.t.toFixed(1), 'pct', st.pct.toFixed(2));
    if (shot < 3 && st.t > [8, 20, 40][shot]) { await pg.screenshot({ path: out + `/o3-play-${shot}.png` }); shot++ }
  }
  await pg.waitForTimeout(2500); await pg.screenshot({ path: out + '/o4-fire.png' });
  await pg.waitForTimeout(4500); await pg.screenshot({ path: out + '/o4b-imo.png' }); await pg.waitForTimeout(3000); await pg.screenshot({ path: out + '/o5-result.png' });
  const G = await pg.evaluate(() => ({ ph: __T.G.phase, pct: __T.G.final, found: __T.G.found, woke: __T.G.cat.woke, n: __T.G.leaves.length }));
  console.log(JSON.stringify(G)); console.log('errs', errs);
  await b.close();
})();
