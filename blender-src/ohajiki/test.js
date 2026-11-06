// node test.js <html> <outdir> [err] — a real drag shot, then a bot that picks the closest pair and flicks with aim error ±err rad
const { chromium } = require('playwright');
(async () => {
  const [html, out, err] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  const p = await pg.evaluate(() => { const p = __T.G.ps[0]; const cv = document.getElementById('cv').getBoundingClientRect(); return [p.x, p.y] });
  const sc = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return [S, (r.width - 720 * S) / 2, (r.height - 1280 * S) / 2] });
  const X = p[0] * sc[0] + sc[1], Y = p[1] * sc[0] + sc[2];
  await pg.mouse.move(X, Y); await pg.mouse.down(); await pg.mouse.move(X + 10, Y + 40, { steps: 5 }); await pg.screenshot({ path: out + '/c2-aim.png' }); await pg.mouse.up();
  await pg.waitForTimeout(2500);
  console.log('real', await pg.evaluate(() => [__T.G.lives, __T.G.got, __T.G.state]));
  await pg.evaluate(([E, PE]) => { const T = __T, G = T.G;
    (function bot() { if (G.phase === 'play' && G.state === 'aim') { const ps = G.ps.filter(p => !p.off); let best = null, bd = 1e9;
        for (const a of ps) for (const b of ps) if (a !== b) { const d = Math.hypot(a.x - b.x, a.y - b.y); const cx = 360, cy = 568; const out = Math.hypot(b.x - cx, b.y - cy); if (d + out * .3 < bd) { bd = d + out * .3; best = [a, b, d] } }
        if (best) { const [a, b, d] = best, ang = Math.atan2(b.y - a.y, b.x - a.x) + (Math.random() * 2 - 1) * E, need = d - T.PR * 2 + 40, v = (Math.sqrt(2 * T.FRIC * need) * 1.15 + 60) * (1 + (Math.random() * 2 - 1) * PE); T.shoot(a, Math.cos(ang) * v, Math.sin(ang) * v) } }
      requestAnimationFrame(bot) })() }, [+(err || .05), +(process.argv[5] || .3)]);
  await pg.waitForTimeout(8000); await pg.screenshot({ path: out + '/c3-play.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 150000 }).catch(() => {});
  await pg.waitForTimeout(2400); await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, got: __T.G.got, mc: __T.G.maxCombo, r: __T.G.round, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
