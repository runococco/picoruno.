// node test.js <html> <outdir>   — a bot that aims at the nearest reachable pad ahead (leading moving pads) and lets go
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  const T = await pg.evaluate(() => __T.toFrame());
  const S = (x, y) => [T.OX + x * T.S, T.OY + y * T.S];
  let shots = 0;
  for (let n = 0; n < 60; n++) {
    const st = await pg.evaluate(() => { const G = __T.G, f = G.frog; return { ph: G.phase, busy: !!(f.j || f.splash), fx: f.x, fy: f.y, pads: G.pads.filter(p => p.y > f.y + 60 && p.y < f.y + 330 && p.sinkT === 0 && p.type !== 'leaf_old').map(p => ({ x: p.x, y: p.y, vx: p.vx })) } });
    if (st.ph !== 'play') break;
    if (st.busy || !st.pads.length) { await pg.waitForTimeout(150); continue }
    const reach = st.pads.filter(q => Math.hypot(q.x + q.vx * .62 - st.fx, q.y - st.fy) < 320); if (!reach.length) { await pg.waitForTimeout(150); continue }
    const p = reach.sort((a, b) => b.y - a.y)[0];
    const tx = p.x + p.vx * 0.62, ty = p.y; let dx = tx - st.fx, dy = ty - st.fy; const L = Math.hypot(dx, dy); if (L > 335) { dx *= 335 / L; dy *= 335 / L }
    const pull = Math.hypot(dx, dy) / 340 * 230;
    const sx = 360, sy = 900; await pg.mouse.move(...S(sx, sy)); await pg.mouse.down();
    await pg.mouse.move(...S(sx - dx / Math.hypot(dx, dy) * pull, sy + dy / Math.hypot(dx, dy) * pull), { steps: 3 });
    if (shots < 1 && n === 6) { await pg.screenshot({ path: out + '/c2-aim.png' }); shots++ }
    await pg.mouse.up(); await pg.waitForTimeout(300);
    if (n === 14) await pg.screenshot({ path: out + '/c3-jump.png' });
    await pg.waitForTimeout(400);
  }
  await pg.waitForTimeout(500); await pg.screenshot({ path: out + '/c3b.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, m: Math.floor(__T.G.best / 100), lives: __T.G.lives, fly: __T.G.fly, jumps: __T.G.jumps }))));
  console.log('errs', errs); await b.close();
})();
