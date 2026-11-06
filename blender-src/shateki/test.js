// node test.js <html> <outdir>   — drags real pointer aims at prize tops (some low shots), then lets the corks run out
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  const T = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const W = r.width, H = r.height, S = Math.min(W / 720, Math.max(H / 1280, W / 720 * .92)); return { S, OX: (W - 720 * S) / 2, OY: (H - 1280 * S) / 2 } });
  const P = (x, y) => [T.OX + x * T.S, T.OY + y * T.S];
  for (let n = 0; n < 15; n++) {
    const tg = await pg.evaluate((n) => { const G = __T.G; const ps = G.prizes.filter(p => !p.fall && p.pop >= 1); const p = ps.find(q => q.k === 'kinneko') || ps[n % ps.length]; const s = __T.sway(); return { x: p.x - s.x, y: p.y - __T.ph(p.k) * (n % 4 === 3 ? .2 : .88) - s.y } }, n);
    await pg.mouse.move(...P(tg.x, tg.y + 120 + 40)); await pg.mouse.down(); await pg.mouse.move(...P(tg.x, tg.y + 120), { steps: 4 });
    if (n === 2) await pg.screenshot({ path: out + '/c2-aim.png' });
    const s2 = await pg.evaluate(() => __T.sway()); await pg.mouse.move(...P(tg.x - s2.x, tg.y + 120 - s2.y)); await pg.mouse.up();
    await pg.waitForTimeout(n === 5 ? 120 : 650); if (n === 5) await pg.screenshot({ path: out + '/c3-shot.png' });
    if (n === 6) await pg.screenshot({ path: out + '/c3b.png' });
  }
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, hits: __T.G.hits, got: __T.G.got }))));
  console.log('errs', errs); await b.close();
})();
