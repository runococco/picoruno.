// node test.js <html> <outdir>   — a bot that runs the stall: pour, fill what customers want, flip and take out in the golden zone
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  const T = await pg.evaluate(() => __T.toFrame());
  const tap = (x, y) => pg.mouse.click(T.OX + x * T.S, T.OY + y * T.S);
  let shots = 0; const t0 = Date.now();
  while (Date.now() - t0 < 80000) {
    const s = await pg.evaluate(() => ({ ph: __T.G.phase, t: __T.G.t, sel: __T.G.sel, molds: __T.G.molds.map(m => ({ x: m.x, y: m.y, st: m.st, a: m.a, b: m.b, fill: m.fill, ft: m.flipT })),
      want: __T.G.cust.filter(c => c && !c.leave).flatMap(c => c.want.slice(c.got.length)), tubs: __T.TUBS }));
    if (s.ph !== 'play') break;
    let acted = false;
    for (const m of s.molds) {
      if (m.ft > 0) continue;
      if (m.st === 'empty') { await tap(m.x, m.y); acted = true; break }
      if (m.st === 'batter' && !m.fill) {
        const need = s.want.length ? s.want[Math.floor(Math.random() * s.want.length)] : 'anko';
        if (s.sel !== need) { const t = s.tubs.find(t => t.k === need); await tap(t.x, t.y); }
        await tap(m.x, m.y); acted = true; break
      }
      if (m.st === 'batter' && m.a > 0.66) { await tap(m.x, m.y); acted = true; break }
      if (m.st === 'flip' && m.b > 0.66) { await tap(m.x, m.y); acted = true; break }
    }
    if (!acted) await pg.waitForTimeout(60);
    if (shots < 2 && s.t > 12 + shots * 20) { await pg.screenshot({ path: out + `/c2-play${shots}.png` }); shots++ }
  }
  await pg.waitForTimeout(2500); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ yen: __T.G.yen, made: __T.G.made, perfect: __T.G.perfect, happy: __T.G.happy }))));
  console.log('errs', errs); await b.close();
})();
