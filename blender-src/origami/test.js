// node test.js <html> <outdir> [skill] — solves every sheet with real mouse drags along the generator's folds; lower skill adds wrong folds (undone with the button) and thinking time
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(2500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1600);
  const toPx = async (p) => pg.evaluate(([x, y]) => { const r = document.getElementById('cv').getBoundingClientRect(), W = r.width, H = r.height, S = Math.min(W / 720, Math.max(H / 1280, W / 720 * .92)); return [r.left + (W - 720 * S) / 2 + x * S, r.top + (H - 1280 * S) * .5 + y * S] }, p);
  const drag = async (d) => { const a = await toPx(d[0]), c = await toPx(d[1]); await pg.mouse.move(a[0], a[1]); await pg.mouse.down(); for (let i = 1; i <= 8; i++) { await pg.mouse.move(a[0] + (c[0] - a[0]) * i / 8, a[1] + (c[1] - a[1]) * i / 8); await pg.waitForTimeout(25) } await pg.mouse.up(); await pg.waitForTimeout(500) };
  let shots = 0, fails = 0;
  for (let sheet = 0; sheet < 12; sheet++) {
    await pg.waitForFunction(() => __T.G.state === 'fold' || __T.G.phase !== 'play', null, { timeout: 10000 }).catch(() => {});
    if (await pg.evaluate(() => __T.G.phase !== 'play')) break;
    await pg.waitForTimeout((1 - K) * 4000 + 300);
    const n = await pg.evaluate(() => __T.G.seq.length);
    if (Math.random() > K) { const d = await pg.evaluate(() => { const ms = __T.moves(__T.G.layers, true); const m = ms[Math.floor(Math.random() * ms.length)]; return __T.dragFor(m.L, m.s) }); if (d) { await drag(d); const u = await toPx([150, 1030]); await pg.mouse.click(u[0], u[1]); await pg.waitForTimeout(300) } }
    for (let i = 0; i < n; i++) { const d = await pg.evaluate((i) => { const s = __T.G.seq[i]; return __T.dragFor(s.L, s.s) }, i); if (!d) { fails++; break } await drag(d);
      if (sheet === 6 && i === 0 && shots++ === 0) await pg.screenshot({ path: out + '/c3-mid.png' }) }
    const ok = await pg.evaluate(() => __T.G.state === 'done'); if (!ok) { fails++; const p = await toPx([580, 1030]); await pg.mouse.click(p[0], p[1]) }
    await pg.waitForTimeout(400);
  }
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 20000 }).catch(() => {});
  await pg.waitForTimeout(1800); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, stars: __T.G.stars, perfect: __T.G.perfect, t: __T.G.total.toFixed(0) }))), 'fails', fails);
  console.log('errs', errs); await b.close();
})();
