// node test.js <html> <outdir> [skill] — a real dip-and-lift, then a bot that picks a loop it can afford, glides there above water, dips close and lifts (skill = care + aim)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  const sc = 390 / 720, oy = (780 - 1280 * sc) / 2; const P = (x, y) => [x * sc, oy + y * sc];
  await pg.mouse.move(...P(360, 700)); await pg.mouse.down(); await pg.mouse.move(...P(300, 650), { steps: 8 }); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c2-dip.png' }); await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; let tgt = null, pos = [360, 1100 + T.HOOK_DY], st = 'pick', wait = 0;
    (function bot() { if (G.phase === 'play' && !G.lift && G.snapT <= 0) {
      if (st === 'pick') { const ok = G.balls.filter(b => b.sunk <= 0 && b.w < G.str - .05 * K - .02); const pool = ok.length ? ok : G.balls.filter(b => b.sunk <= 0);
        pool.sort((a, b) => (b.p / (Math.hypot(...T.loopPos(b).map((v, i) => v - pos[i])) + 200)) - (a.p / (Math.hypot(...T.loopPos(a).map((v, i) => v - pos[i])) + 200)));
        tgt = K < .5 ? pool[Math.floor(Math.random() * pool.length)] : pool[0]; if (tgt) st = 'go' }
      if (st === 'go') { if (!G.balls.includes(tgt) || tgt.sunk > 0) { st = 'pick'; if (G.hook) T.release() } else {
        const [lx, ly] = T.loopPos(tgt), dx = lx - pos[0], dy = ly - pos[1], d = Math.hypot(dx, dy), sp = (6 + 10 * K);
        // hover outside the water until close (careful bots), clumsy ones drag the hook through
        if (d > sp) { pos[0] += dx / d * sp; pos[1] += dy / d * sp } else { pos[0] = lx; pos[1] = ly }
        const aimErr = (1 - K) * 26 * Math.sin(G.t * 3);
        if (d < 30 || K < .5) { if (!G.hook) T.press(pos[0] + aimErr, pos[1] - T.HOOK_DY); else T.move(pos[0] + aimErr, pos[1] - T.HOOK_DY) } else if (G.hook) T.release();
        if (G.hook && d < 6) { T.release(); st = 'pick' } } } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(25000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 240000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, n: __T.G.n, best1: __T.G.best1, gold: __T.G.goldN, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
