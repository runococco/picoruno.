// node test.js <html> <outdir> [skill] — real taps on a fruit and a crow, then a bot that shoos pecking crows and picks the ripest
// orange persimmon (skill = reaction lag and how sure it is about the colour)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: (r.width - 720 * S) / 2, oy: (r.height - 1280 * S) / 2 } });
  const f = await pg.evaluate(() => { const f = __T.G.fruits.find(f => f && f.g >= 1); return f ? __T.SL[f.i] : [300, 360] });
  await pg.mouse.click(box.ox + f[0] * box.S, box.oy + f[1] * box.S); await pg.waitForTimeout(250); await pg.screenshot({ path: out + '/c2-reach.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0; const lag = (.12 + (1 - K) * .6) * 1000, lo = .62 - (1 - K) * .2;
    (function bot() { const now = performance.now(); if (G.phase === 'play' && now > next) {
        const c = G.crows.find(c => c.st === 'peck' || (c.st === 'come' && K > .7 && c.y > 100));
        if (c) { T.tap(c.x + (Math.random() - .5) * 20, c.y); next = now + lag }
        else if (G.pole.st === 'idle') { let best = null, br = -1; for (const f of G.fruits) if (f && f.g >= 1 && f.r >= lo && f.r < 1.05 && f.r > br) { br = f.r; best = f }
          if (best) { const [x, y] = T.SL[best.i]; T.tap(x + (Math.random() - .5) * 30, y); next = now + lag } } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(28000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 60000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, picked: __T.G.picked, sweet: __T.G.sweet, stolen: __T.G.stolen, dropped: __T.G.dropped }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
