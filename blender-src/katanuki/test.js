// node test.js <html> <outdir>   — real mouse trace on part of plate 1, then a bot traces (one plate sloppy, one too fast)
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  const S = 390 / 720, OY = (780 - 1280 * S) / 2, f = (x, y) => [x * S, y * S + OY];
  const pts = await pg.evaluate(() => __T.G.pts.map(p => [p[0] - __T.OFF[0], p[1] - __T.OFF[1]]));
  let [x, y] = f(...pts[0]); await pg.mouse.move(x, y); await pg.mouse.down();
  for (let i = 1; i < pts.length * .45; i++) { [x, y] = f(...pts[i]); await pg.mouse.move(x, y); await pg.waitForTimeout(12) }
  await pg.screenshot({ path: out + '/c2-carve.png' }); await pg.mouse.up();
  console.log('progress', await pg.evaluate(() => __T.progress().toFixed(2)), 'stress', await pg.evaluate(() => __T.G.stress | 0));
  const trace = (mode) => pg.evaluate(async (mode) => { const T = __T, G = T.G, P = G.pts.slice(); T.press(P[0][0], P[0][1]);
    for (let i = 1; i <= P.length + 4 && G.phase === 'play'; i++) { const p = P[i % P.length]; const n = mode === 'sloppy' && i % 40 > 30 ? 45 : 0; T.moveTo(p[0] + n, p[1] + n, mode === 'fast' ? .002 : .016); if (i % 6 === 0) await new Promise(r => setTimeout(r, 0)) }
    T.release(); return { ph: G.phase, prog: T.progress().toFixed(3), cracks: G.cracks.length } }, mode);
  console.log('p1', JSON.stringify(await trace('ok')));
  await pg.waitForTimeout(400); await pg.screenshot({ path: out + '/c3-pop.png' });
  for (const mode of ['sloppy', 'ok', 'fast', 'ok']) { await pg.waitForFunction(() => __T.G.phase === 'play' || __T.G.phase === 'end', null, { timeout: 8000 }); await pg.waitForTimeout(300); console.log(mode, JSON.stringify(await trace(mode))); if (mode === 'sloppy') { await pg.waitForTimeout(200); await pg.screenshot({ path: out + '/c4-sloppy.png' }) } if (mode === 'fast') { await pg.waitForTimeout(150); await pg.screenshot({ path: out + '/c5-broke.png' }) } }
  await pg.waitForFunction(() => __T.G.phase === 'end', null, { timeout: 10000 }); await pg.waitForTimeout(2200);
  await pg.screenshot({ path: out + '/c6-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ s: __T.G.score, res: __T.G.res }))));
  console.log('errs', errs); await b.close();
})();
