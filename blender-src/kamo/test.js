// node test.js <html> <outdir> [skill] — a real drag, then a bot that collects ducklings (bigger trains with skill),
// waits for logs to pass, and swims home (skill = how long a train it risks and how well it watches logs)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  await pg.mouse.move(195, 480); await pg.mouse.down(); await pg.mouse.move(150, 300, { steps: 20 }); await pg.waitForTimeout(900); await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; const want = Math.round(3 + K * 4), look = .3 + K * .7;
    (function bot() { if (G.phase === 'play') { const m = G.mom; let tx, ty;
        const goHome = G.chain.length >= want || (G.chain.length && G.left < 9) || (!G.loose.length && G.chain.length);
        if (goHome) { tx = T.NEST[0]; ty = T.Y1 + 30 } else { let bd = 1e9; for (const c of G.loose) { const d = Math.hypot(c.x - m.x, c.y - m.y); if (d < bd) { bd = d; tx = c.x; ty = c.y } } }
        if (tx == null) { tx = m.x; ty = m.y }
        // wait if a log will cross just ahead (or the train)
        const a = Math.atan2(ty - m.y, tx - m.x), ax = m.x + Math.cos(a) * 110, ay = m.y + Math.sin(a) * 110;
        let block = false; for (const l of G.logs) { const fut = { ...l, x: l.x + l.vx * look }; if (T.segDist(ax, ay, fut) < 70 || T.segDist(m.x, m.y, fut) < 60) block = true;
          if (K > .5) for (const c of G.chain) if (T.segDist(c.x, c.y, fut) < 46) block = block || Math.abs(l.y - m.y) < 200 && false }
        if (block) T.steer(null, null, false); else T.steer(tx, ty, true) }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(30000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 70000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, saved: __T.G.saved, best: __T.G.bestRun, hits: __T.G.hits, t: __T.G.t.toFixed(0) }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
