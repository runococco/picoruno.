// node test.js <html> <outdir> [skill] — a real mouse drag of one yarn ball, then a bot that moves balls back to the generator's
// untangled layout one at a time (skill = pause between moves; it stands in for how quickly a player sees the layout)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: (r.width - 720 * S) / 2, oy: (r.height - 1280 * S) / 2 } });
  await pg.screenshot({ path: out + '/c2-start.png' });
  const n0 = await pg.evaluate(() => [__T.G.nodes[0].x, __T.G.nodes[0].y, __T.G.nodes[0].sx, __T.G.nodes[0].sy]);
  await pg.mouse.move(box.ox + n0[0] * box.S, box.oy + n0[1] * box.S); await pg.mouse.down(); await pg.mouse.move(box.ox + n0[2] * box.S, box.oy + n0[3] * box.S, { steps: 15 }); await pg.mouse.up();
  console.log('drag moved', await pg.evaluate(() => [Math.round(__T.G.nodes[0].x), Math.round(__T.G.nodes[0].y), __T.G.moves]), 'target', n0.slice(2).map(Math.round));
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0; const gap = (.35 + (1 - K) * 1.6) * 1000;
    (function bot() { const now = performance.now(); if (G.phase === 'play' && G.clearT <= 0 && now > next) {
        const i = G.nodes.findIndex(n => Math.hypot(n.x - n.sx, n.y - n.sy) > 3);
        if (i >= 0) { const n = G.nodes[i]; if (T.grab(n.x, n.y) && G.drag === i) { T.move(n.sx, n.sy); T.drop() } else { n.x = n.sx; n.y = n.sy } next = now + gap } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(40000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, cleared: __T.G.cleared, balls: __T.G.balls, lv: __T.G.lv }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
