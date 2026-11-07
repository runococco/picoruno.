// node test.js <html> <outdir> [skill] — a real mouse drag, then a bot that slides containers under falling drops
// and empties them when nearly full (skill = how often it reacts and how well it plans)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.stack.slice(0, 300))); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(700);
  await pg.screenshot({ path: out + '/c2-start.png' });
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: r.left + (r.width - 720 * S) / 2, oy: r.top + (r.height - 1280 * S) / 2 } });
  const p0 = await pg.evaluate(() => __T.G.pots[0].x);
  await pg.mouse.move(box.ox + p0 * box.S, box.oy + 1000 * box.S); await pg.mouse.down(); await pg.mouse.move(box.ox + 120 * box.S, box.oy + 1000 * box.S, { steps: 6 }); await pg.mouse.up();
  await pg.waitForTimeout(300); console.log('mouse drag pot0 x', await pg.evaluate(() => Math.round(__T.G.pots[0].x)));
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0; const lag = (.05 + (1 - K) * .35) * 1000;
    (function bot() { const now = performance.now(); if (G.phase === 'play' && now > next) { next = now + lag;
        const used = new Set(); const want = [];
        const ev = G.drops.map(d => ({ x: d.x, y: d.y })).concat(G.leaks.filter(l => l.on && l.form > 0).map(l => ({ x: l.x, y: -100 }))).sort((a, b) => b.y - a.y);
        for (const e of ev) { if (want.some(w => w.x === e.x)) continue; let best = null, bd = 1e9;
          for (const p of G.pots) { if (used.has(p) || p.out > 0 || p.fill >= p.cap - (K < .5 ? 0 : 1)) continue; const d = Math.abs(p.x - e.x) + (Math.random() < (1 - K) * .3 ? 300 : 0); if (d < bd) { bd = d; best = p } }
          if (best) { used.add(best); want.push({ p: best, x: e.x }) } }
        for (const w of want) { if (Math.abs(w.p.x - w.x) > 4) { T.down(w.p.x, 1000); T.move(w.x + (Math.random() - .5) * (1 - K) * 40, 1000); G.drag && (G.drag.moved = true); T.up() } }
        for (const p of G.pots) if (!used.has(p) && p.fill >= p.cap * (K < .5 ? 1 : .6)) { T.empty(p) } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(25000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 240000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, t: Math.round(__T.G.t), lv: __T.G.lv, caught: __T.G.caught, combo: __T.G.maxCombo }));
  await pg.waitForTimeout(2800); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
