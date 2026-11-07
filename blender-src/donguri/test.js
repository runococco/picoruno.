// node test.js <html> <outdir> [skill] — real taps on the levers, then a bot that sets each lever for the next item that will
// reach it (skill = reaction lag and a small chance to misjudge)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: (r.width - 720 * S) / 2, oy: (r.height - 1280 * S) / 2 } });
  for (const [x, y] of [[360, 430], [190, 650]]) { await pg.mouse.click(box.ox + x * box.S, box.oy + y * box.S); await pg.waitForTimeout(300) }
  await pg.screenshot({ path: out + '/c2-tap.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G, P = T.P; const lag = (.08 + (1 - K) * .5) * 1000; const next = { A: 0, B: 0, C: 0 }; const wrong = new Set();
    const want = (n, bin) => n === 'A' ? (bin[0] === 'L' ? 0 : 1) : (bin.endsWith('1') ? 0 : 1);
    function eta(it, n) { // rough distance (px) until the item reaches node n, or Infinity
      if (it.st === 'fall') { if (n === 'A') return P.A[1] - it.y; const nb = T.KIND[it.k].bin; const via = nb[0] === 'L' ? 'B' : 'C'; return n === via ? (P.A[1] - it.y) + 280 : Infinity }
      if (it.st === 'roll' && it.to === n) { const a = P[it.from], b = P[it.to]; return Math.hypot(b[0] - a[0], b[1] - a[1]) - it.d } return Infinity }
    (function bot() { const now = performance.now(); if (G.phase === 'play') { for (const n of ['A', 'B', 'C']) { if (now < next[n]) continue;
          let first = null, fe = Infinity; for (const it of G.items) { const e = eta(it, n); if (e < fe) { fe = e; first = it } }
          if (!first) continue; let w = want(n, T.KIND[first.k].bin); if (!first.judged) { first.judged = {}; } if (first.judged[n] === undefined) first.judged[n] = Math.random() < (1 - K) * .12; if (first.judged[n]) w ^= 1;
          if (G.sw[n] !== w) { T.toggle(n); next[n] = now + lag } } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(30000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 70000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, done: __T.G.done, combo: __T.G.maxCombo, hearts: __T.G.hearts, t: __T.G.t.toFixed(0) }));
  if (st.ph === 'play') await pg.evaluate(() => { __T.G.hearts = 1; __T.G.sw.A = 1; __T.G.sw.C = 0; __T.G.items.push({ k: 'acorn', st: 'fall', x: 360, y: 300, vy: 0, rot: 0, from: null, to: 'A', d: 0 }) });
  await pg.waitForTimeout(4500); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
