// node test.js <html> <outdir>   — checks every level generates and is solvable, then plays level 1 to the end
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/c1-title.png' });
  const lv = await pg.evaluate(() => { const r = []; for (let L = 0; L < 12; L++) { const P = __T.generate(L, 1000 + L * 37); r.push(P ? { L, mirrors: P.n, buds: P.buds.length, par: P.par } : { L, fail: 1 }) } const d = new Date(); const k = d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate(); const D = __T.generate(8, k * 7 + 13); r.push(D ? { daily: 1, par: D.par, n: D.n } : { daily: 'fail' }); return r });
  console.log(JSON.stringify(lv));
  for (const L of [0, 6, 11]) {
    await pg.evaluate(L => __T.play(L, false), L); await pg.waitForTimeout(500);
    if (L === 6) await pg.screenshot({ path: out + '/c2-start.png' });
    const T = await pg.evaluate(() => __T.toFrame());
    // solve by asking for hints and tapping the suggested mirror
    for (let k = 0; k < 20; k++) {
      const s = await pg.evaluate(() => { const G = __T.G; if (G.phase !== 'play') return null; const q = __T.bestFix(G.P, G.ori); let cell = -1; G.P.grid.forEach((c, i) => { if (c.t === 'mirror' && c.m === q) cell = i }); return { cell, C: 6 } });
      if (!s || s.cell < 0) break;
      const i = s.cell % 6, j = Math.floor(s.cell / 6);
      const p = await pg.evaluate(([i, j]) => [130 + i * 92, 348.2 + j * 83.38 - 10], [i, j]);
      await pg.mouse.click(T.OX + p[0] * T.S, T.OY + p[1] * T.S); await pg.waitForTimeout(250);
    }
    await pg.waitForTimeout(800); if (L === 6) await pg.screenshot({ path: out + '/c3-win.png' });
    await pg.waitForTimeout(1500); if (L === 6) await pg.screenshot({ path: out + '/c4-result.png' });
    console.log(L, JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, taps: __T.G.taps, par: __T.G.P.par }))));
  }
  console.log('errs', errs); await b.close();
})();
