// node test.js <html> <outdir> [skill] — a real mouse tap, then a bot that remembers the peek with probability = skill
// and otherwise opens unknown doors
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.stack.slice(0, 300))); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(700);
  await pg.screenshot({ path: out + '/c2-peek.png' });
  await pg.waitForTimeout(1400);
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: r.left + (r.width - 720 * S) / 2, oy: r.top + (r.height - 1280 * S) / 2 } });
  const i0 = await pg.evaluate(() => __T.G.cells.findIndex(c => c.k)); const cx = 40 + 160 * (i0 % 4 + .5), cy = 176 + 176 * (Math.floor(i0 / 4) + .5);
  await pg.mouse.click(box.ox + cx * box.S, box.oy + cy * box.S); await pg.waitForTimeout(200);
  console.log('mouse open', await pg.evaluate(() => __T.G.sel.length));
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0, mem = new Map(), stage = -1; const lag = (.35 + (1 - K) * .4) * 1000;
    (function bot() { const now = performance.now();
      if (G.phase === 'play' && G.stage !== stage && G.peek > 0) { stage = G.stage; mem = new Map(); G.cells.forEach((c, i) => { if (c.k && Math.random() < K) mem.set(i, c.k) }) }
      if (G.phase === 'play' && G.peek <= 0 && G.lock <= 0 && G.between <= 0 && now > next) { next = now + lag;
        const open = G.cells.map((c, i) => i).filter(i => G.cells[i].k && !G.cells[i].done && !G.sel.includes(i));
        if (G.sel.length === 0) { // a known pair first
          const seen = {}; let pair = null; for (const [i, k] of mem) { if (G.cells[i].done) continue; if (seen[k] != null) { pair = [seen[k], i]; break } seen[k] = i }
          const i = pair ? pair[0] : (open.find(i => !mem.has(i)) ?? open[0]); if (i != null) { mem.set(i, G.cells[i].k); T.pick(i) } }
        else { const a = G.sel[0], k = G.cells[a].k; let j = [...mem].find(([i, kk]) => kk === k && i !== a && !G.cells[i].done); j = j ? j[0] : (open.find(i => !mem.has(i)) ?? open[0]); if (j != null) { mem.set(j, G.cells[j].k); T.pick(j) } } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(15000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase === 'end', null, { timeout: 200000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, stage: __T.G.stage, pairs: __T.G.pairs, misses: __T.G.misses, combo: __T.G.maxCombo, t: Math.round(__T.G.t) }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
