// node test.js <html> <outdir> [skill] — a real drag, then a bot (skill 1 = moves the cushion just ahead of the drifting sun as soon as it is about to leave it)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  const p = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(), S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)), OX = (r.width - 720 * S) / 2, OY = (r.height - 1280 * S) / 2, G = __T.G; return { x: G.cat.x * S + OX, y: G.cat.y * S + OY, sx: G.sun.x * S + OX, sy: G.sun.y * S + OY } });
  await pg.mouse.move(p.x, p.y); await pg.mouse.down(); await pg.mouse.move(p.sx, p.sy, { steps: 15 }); await pg.screenshot({ path: out + '/c2-drag.png' }); await pg.mouse.up();
  await pg.waitForTimeout(2500); await pg.screenshot({ path: out + '/c3-sun.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let lt = performance.now(), wait = 0, mv = null;
    (function bot(n) { const dt = Math.min(.05, (n - lt) / 1000) || .016; lt = n; if (G.phase === 'play') { const c = G.cat, s = G.sun;
      if (mv) { const dx = mv[0] - c.x, dy = mv[1] - c.y, d = Math.hypot(dx, dy), st = Math.min(d, 1600 * dt); if (d < 6) { T.letGo(); mv = null } else { if (!G.drag) T.grabAt(c.x, c.y); T.dragTo(c.x + dx / d * st, c.y + dy / d * st) } }
      else { const inside = T.inPatch(s, c.x, c.y, T.SW - 90, T.SH - 90); if (!inside) { wait += dt; if (wait > (1 - K) * 2.5) { wait = 0; const k = Math.min(1, 110 / Math.max(1, Math.hypot(s.tx - s.x, s.ty - s.y))); mv = [s.x + (s.tx - s.x) * k * K, s.y + (s.ty - s.y) * k * K] } } else wait = 0 } }
      requestAnimationFrame(bot) })(performance.now()) }, K);
  await pg.waitForFunction(() => __T.G.star && __T.G.star.t > .5, null, { timeout: 40000 }).catch(() => {}); await pg.screenshot({ path: out + '/c4-star.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 90000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: Math.floor(__T.G.score), sun: __T.G.sunT.toFixed(0), long: __T.G.longest.toFixed(0), st: __T.G.starN }))));
  console.log('errs', errs); await b.close();
})();
