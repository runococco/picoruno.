// node test.js <html> <outdir> [skill] — a real press-hold-release, then a bot that picks the landing spot that flips the most and lets go in the green band (skill = aim + timing error)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1000);
  const sc = 390 / 720, oy = (780 - 1280 * sc) / 2; const P = (x, y) => [x * sc, oy + y * sc];
  const c0 = await pg.evaluate(() => { const c = __T.G.cards[0]; return [c.x + 95, c.y] });
  await pg.mouse.move(...P(...c0)); await pg.mouse.down(); await pg.waitForTimeout(700); await pg.screenshot({ path: out + '/c2-charge.png' }); await pg.mouse.up();
  await pg.waitForTimeout(500); await pg.screenshot({ path: out + '/c2b-hit.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G, CR = T.CR; let plan = null;
    function g() { return (Math.random() + Math.random() + Math.random() - 1.5) / .5 }
    (function bot() { if (G.phase === 'play') {
      if (G.state === 'aim' && !G.charging && !plan) { const up = G.cards.filter(c => c.st === 'up'); let best = null;
        for (const c of up) for (let a = 0; a < 6.28; a += .26) { const x = c.x + Math.cos(a) * (CR + 4), y = c.y + Math.sin(a) * (CR + 4); let v = 0, bad = false;
          for (const o of up) { const d = Math.hypot(o.x - x, o.y - y); if (d < CR * .9) { bad = true; break } const e = d - CR, R = 25 + 55 * .84, f = .84 * Math.max(0, 1 - Math.max(0, e) / R) * (e < 0 ? 1.15 : 1); if (f > o.hp) v += T.KIND[o.k].p }
          if (!bad && (!best || v > best.v)) best = { x, y, v } }
        if (best) { plan = { x: best.x + g() * 26 * (1 - K), y: best.y + g() * 26 * (1 - K), p: .84 + g() * .1 * (1 - K) }; T.press(plan.x, plan.y) } }
      if (plan && G.charging && Math.abs(G.pw - plan.p) < .03) { T.release(); plan = null }
      if (G.state !== 'aim') plan = null }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForFunction(() => __T.G.round >= 1, null, { timeout: 120000 }).catch(() => {}); await pg.waitForTimeout(3000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 200000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, got: __T.G.got, multi: __T.G.multi, thrown: __T.G.thrown }))));
  console.log('errs', errs); await b.close();
})();
