// node test.js <html> <outdir>   — a bot that rolls a body, rolls a head and pushes it onto the body, again and again
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  const T = await pg.evaluate(() => __T.toFrame());
  const scr = (x, y) => [T.OX + x * T.S, T.OY + y * T.S];
  const W = (wx, wy, r = 20) => pg.evaluate(([wx, wy, r]) => [__T.sxOf(wx), __T.syOf(wy) - r * __T.CE], [wx, wy, r]);
  const st = () => pg.evaluate(() => ({ ph: __T.G.phase, balls: __T.G.balls.map(b => ({ x: b.x, y: b.y, r: b.r })), men: __T.G.men.length, left: __T.snowLeft() }));
  const spots = [[-40, -620], [-170, -230], [40, 380], [120, -420], [-120, 40], [200, 60]];
  let shot = 0;
  async function roll(sx, sy, target) {
    let [fx, fy] = await W(sx, sy); await pg.mouse.move(...scr(fx, fy)); await pg.mouse.down();
    let a = 0, R = 30;
    for (let k = 0; k < 1200; k++) {
      const s = await st(); if (s.ph !== 'play') { await pg.mouse.up(); return null }
      const me = s.balls.sort((p, q) => Math.hypot(p.x - sx, p.y - sy) - Math.hypot(q.x - sx, q.y - sy))[0]; if (!me) break;
      if (me.r >= target) { await pg.mouse.up(); return me }
      a += 0.35; R = Math.min(115, R + 1.2);
      const [x, y] = await W(sx + Math.cos(a) * R, sy + Math.sin(a) * R * 1.0, me.r); await pg.mouse.move(...scr(x, y), { steps: 2 }); await pg.waitForTimeout(30);
    }
    await pg.mouse.up(); return null
  }
  for (const [sx, sy] of spots) {
    const body = await roll(sx, sy, 100); if (!body) break;
    const head = await roll(sx + (sx < 0 ? 200 : -200), sy + 30, 40); if (!head) break;
    // push the head into the body
    let [hx, hy] = await W(head.x, head.y, head.r); await pg.mouse.move(...scr(hx, hy)); await pg.mouse.down();
    for (let k = 0; k < 30; k++) { const s = await st(); if (s.ph !== 'play') break; const hb = s.balls.find(q => Math.abs(q.r - head.r) < 15 && q.r < 90); if (!hb) break;
      const [tx, ty] = await W(body.x, body.y, head.r); await pg.mouse.move(...scr(tx, ty), { steps: 3 }); await pg.waitForTimeout(40) }
    await pg.mouse.up(); await pg.waitForTimeout(700);
    if (shot < 2) { await pg.screenshot({ path: out + `/c2-play${shot}.png` }); shot++ }
    const s = await st(); console.log('men', s.men, 'snow', s.left.toFixed(0));
    if (s.ph !== 'play') break;
  }
  await pg.waitForTimeout(Math.max(0, 1)); await pg.screenshot({ path: out + '/c3-late.png' });
  for (let k = 0; k < 80; k++) { const s = await st(); if (s.ph !== 'play') break; await pg.waitForTimeout(500) }
  await pg.waitForTimeout(2500); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ score: __T.G.score, men: __T.G.men.length, perfect: __T.G.perfect }))));
  console.log('errs', errs); await b.close();
})();
